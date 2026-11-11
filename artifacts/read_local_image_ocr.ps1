param([Parameter(Mandatory=$true)][string]$ImagePath)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null=[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$null=[Windows.Globalization.Language,Windows.Globalization,ContentType=WindowsRuntime]
$asTask=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {$_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'})[0]
function Await($op,$type){$t=$asTask.MakeGenericMethod($type).Invoke($null,@($op));$t.Wait();$t.Result}
$f=Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$s=Await ($f.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$d=Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($s)) ([Windows.Graphics.Imaging.BitmapDecoder])
$b=Await ($d.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$e=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$r=Await ($e.RecognizeAsync($b)) ([Windows.Media.Ocr.OcrResult])
[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
foreach($line in $r.Lines){foreach($w in $line.Words){Write-Output ($w.Text+' | '+$w.BoundingRect.ToString())}}
