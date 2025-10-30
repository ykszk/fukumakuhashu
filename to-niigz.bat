set BIN=%~dp0..\dcm2niix.exe
set INPUT=%1
set OUTPUT=%~dp0..\..\data\dcm2niix\

echo Converting DICOM files in %INPUT% to NIfTI format...
echo Output directory: %OUTPUT%

%BIN% -z i -o %OUTPUT% %INPUT%

pause