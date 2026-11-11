Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null=[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
$null=[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime]
$null=[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]
$asTask=([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1)
function Await($op,$type) { $t=$asTask.MakeGenericMethod($type).Invoke($null,@($op));$t.Wait();$t.Result }
$paths=@('D:\smart_fans\artifacts\user_module_sources\asr_spec_rotated.png')
$engine=[Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$result=@()
foreach($path in $paths){
 $file=Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($path)) ([Windows.Storage.StorageFile])
 $stream=Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
 $dec=Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
 $bmp=Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
 $ocr=Await ($engine.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
 $lines=@();foreach($line in $ocr.Lines){$words=@();foreach($w in $line.Words){$words+=@{text=$w.Text;x=$w.BoundingRect.X;y=$w.BoundingRect.Y;width=$w.BoundingRect.Width;height=$w.BoundingRect.Height}};$lines+=@{text=$line.Text;words=$words}}
 $result+=@{path=$path;text=$ocr.Text;lines=$lines}
}
$result | ConvertTo-Json -Depth 10 | Set-Content -Encoding utf8 'D:\smart_fans\artifacts\user_module_sources\asr_spec_rotated_ocr.json'
