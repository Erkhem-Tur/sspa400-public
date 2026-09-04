param(
  [Parameter(Mandatory = $true)][string]$DocxPath,
  [string]$JsonPath = "lms/static/lms/terminology.json"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Normalize-Term([string]$Value) {
  return (($Value.ToLowerInvariant() -replace '[^a-z0-9]+', ' ').Trim())
}

function Get-Module([int]$RowNumber) {
  if ($RowNumber -le 23) { return "Organization & protective units" }
  if ($RowNumber -le 41) { return "Motorcade & close protection" }
  if ($RowNumber -le 69) { return "Equipment & weapons" }
  if ($RowNumber -le 91) { return "Airport & travel" }
  if ($RowNumber -le 117) { return "Protection actions & screening" }
  if ($RowNumber -le 142) { return "Site security & advance work" }
  if ($RowNumber -le 161) { return "Interagency & emergency response" }
  if ($RowNumber -le 191) { return "Security screening phrases" }
  if ($RowNumber -le 249) { return "Hotel & service English" }
  return "Hospitality & dining"
}

function Clean-Cell([string]$Value) {
  return (($Value -replace [char]0xA0, ' ' -replace '\s+', ' ').Trim(' ', '/', '-'))
}

function Clean-English([string]$Value) {
  $parts = @($Value -split '/' | Where-Object { $_ -notmatch '[А-Яа-яӨөҮүЁё]' } | ForEach-Object { Clean-Cell $_ })
  $cleaned = Clean-Cell ($parts -join ' / ')
  return (Clean-Cell ($cleaned -replace '-\s*[А-Яа-яӨөҮүЁё].*$', ''))
}

$resolvedDocx = (Resolve-Path $DocxPath).Path
$resolvedJson = (Resolve-Path $JsonPath).Path
$archive = [IO.Compression.ZipFile]::OpenRead($resolvedDocx)
try {
  $entry = $archive.GetEntry('word/document.xml')
  $reader = [IO.StreamReader]::new($entry.Open())
  try { [xml]$xml = $reader.ReadToEnd() } finally { $reader.Dispose() }
} finally { $archive.Dispose() }

$ns = [Xml.XmlNamespaceManager]::new($xml.NameTable)
$ns.AddNamespace('w', 'http://schemas.openxmlformats.org/wordprocessingml/2006/main')
$data = Get-Content -Raw -Encoding UTF8 $resolvedJson | ConvertFrom-Json
$importSource = "SSPA professional vocabulary compilation (15 unique source documents)"
foreach ($existing in $data.items) {
  if ($existing.source_reference -ne $importSource) { continue }
  $existing.front = Clean-English $existing.front
  $isExistingPhrase = $existing.item_type -eq 'operational_phrase'
  $existing.definition_en = if ($isExistingPhrase) {
    'An operational phrase used to communicate the Mongolian meaning: "{0}".' -f $existing.back_mn
  } else {
    'A professional English term meaning "{0}" in protection, travel, or service contexts.' -f $existing.back_mn
  }
  $existing.example_en = if ($isExistingPhrase) { $existing.front } else { 'The team reviewed "{0}" during the duty briefing.' -f $existing.front }
  $existing.audio_script = "$($existing.front). $($existing.definition_en) $($existing.example_en)"
}
$seen = @{}
$deduped = [System.Collections.Generic.List[object]]::new()
foreach ($item in $data.items) {
  $existingKey = Normalize-Term $item.front
  if (!$existingKey -or $seen.ContainsKey($existingKey)) { continue }
  $seen[$existingKey] = $true
  $deduped.Add($item)
}
$data.items = @($deduped)
$nextId = [int](($data.items | ForEach-Object { [int]($_.item_id -replace '\D', '') } | Measure-Object -Maximum).Maximum) + 1
$added = [System.Collections.Generic.List[object]]::new()
$rowNumber = 0

foreach ($row in $xml.SelectNodes('//w:tr', $ns)) {
  $rowNumber++
  $cells = @()
  foreach ($cell in $row.SelectNodes('./w:tc', $ns)) {
    $paragraphs = @()
    foreach ($paragraph in $cell.SelectNodes('./w:p', $ns)) {
      $text = Clean-Cell (($paragraph.SelectNodes('.//w:t', $ns) | ForEach-Object { $_.InnerText }) -join '')
      if ($text) { $paragraphs += $text }
    }
    $cells += (Clean-Cell ($paragraphs -join ' / '))
  }

  $english = ''
  $mongolian = ''
  if ($cells.Count -ge 3 -and $cells[0] -match '^\s*\d+\s*$') {
    $mongolian = $cells[1]
    $english = $cells[2]
  } elseif ($cells.Count -ge 2) {
    if ($cells[0] -match '[А-Яа-яӨөҮүЁё]') {
      $mongolian = $cells[0]
      $english = $cells[1]
    } elseif ($cells[1] -match '[А-Яа-яӨөҮүЁё]') {
      $english = $cells[0]
      $mongolian = $cells[1]
    }
  }

  $english = Clean-English $english
  $mongolian = Clean-Cell $mongolian
  if (!$english -or !$mongolian -or $english.Length -gt 180 -or $mongolian.Length -gt 220) { continue }
  if ($english -match 'тогтсон хэллэг|Доорхи өгүүлбэр|Европ болон|Америк болон') { continue }

  $key = Normalize-Term $english
  if (!$key -or $seen.ContainsKey($key)) { continue }
  $seen[$key] = $true
  $module = Get-Module $rowNumber
  $isPhrase = $english -match '\s' -and ($english.Split(' ', [StringSplitOptions]::RemoveEmptyEntries).Count -ge 4)
  $type = if ($isPhrase) { 'operational_phrase' } else { 'terminology_flashcard' }
  $difficulty = if ($isPhrase -or $english.Length -gt 35) { 'B1' } else { 'A2' }
  $priority = if ($module -match 'protection|security|weapons|emergency') { 'Core' } else { 'Extended' }
  $definition = if ($isPhrase) {
    'An operational phrase used to communicate the Mongolian meaning: "{0}".' -f $mongolian
  } else {
    'A professional English term meaning "{0}" in protection, travel, or service contexts.' -f $mongolian
  }
  $example = if ($isPhrase) { $english } else { 'The team reviewed "{0}" during the duty briefing.' -f $english }

  $item = [ordered]@{
    item_id = ('T-{0:D3}' -f [int]$nextId)
    module = $module
    item_type = $type
    front = $english
    back_mn = $mongolian
    definition_en = $definition
    example_en = $example
    audio_script = "$english. $definition $example"
    difficulty = $difficulty
    priority = $priority
    tags = "sspa,professional-vocabulary,docx-import"
    source_reference = $importSource
    review_note = "Study the meaning, listen to the pronunciation, then recall it with flashcards."
  }
  $added.Add([pscustomobject]$item)
  $nextId++
}

$data.items = @($data.items) + @($added)
$data.meta.modules = @($data.items.module | Sort-Object -Unique)
$data.meta | Add-Member -NotePropertyName total_items -NotePropertyValue $data.items.Count -Force
$json = $data | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($resolvedJson, $json, [Text.UTF8Encoding]::new($false))
Write-Output "Added $($added.Count) unique translated items; total $($data.items.Count)."
