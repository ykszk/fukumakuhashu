set BIN=%~dp0..\dcm2itk.exe
set INPUT=%1
set OUTPUT=%~dp0..\..\data\dcm2niix\

echo Converting DICOM files in %INPUT% to NIfTI format...
echo Output directory: %OUTPUT%

%BIN% --outdir %OUTPUT% %INPUT%

pause