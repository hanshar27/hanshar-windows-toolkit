# Hanshar Windows Toolkit Release Notes

## Unreleased

- Renamed the packaged EXE, installer, release ZIP, and PyInstaller spec to Hanshar; existing reports remain in their current data folder.
- Added a confirmed Windows standby-memory cache purge with administrator approval.
- Updated the visible application and installer branding to Hanshar Windows Toolkit while preserving persistent data locations.
- Added a System Information page that generates and displays complete MSInfo32 and DxDiag reports.
- Reports are generated in the background and saved locally under `reports/`.
- Replaced the previous themes with one glass-style interface inspired by the Home Assistant dashboard reference.
- Added a Settings slider for Windows acrylic backdrop intensity. Windows controls the blur radius; the slider adjusts the acrylic tint/transparency strength.
- Redesigned the sidebar with flat icon navigation and the dashboard with a warm-charcoal Bento grid, live circular CPU/RAM gauges, network rates, and a performance chart.
- Replaced the dashboard's CPU temperature tile with actual GPU temperature, using `nvidia-smi` for NVIDIA cards and LibreHardwareMonitor/OpenHardwareMonitor as fallback.
- Updated the System Monitor details to remove CPU temperature and show GPU temperature instead.
- Expanded Storage Cleaner with user `%TEMP%`, Windows Temp, Prefetch, and an opt-in Recycle Bin cleanup action.
- Improved Dashboard text wrapping and Quick Action sizing so labels remain readable in smaller windows.
- Made the Storage Cleaner page scroll vertically so the Scan preview and activity log remain reachable when the window is shortened.
- Excluded active PyInstaller temporary runtime folders from Temp cleanup to prevent missing `base_library.zip` errors.

## Version 1.1.0

Hanshar Windows Toolkit is a production-ready Windows desktop utility suite for system monitoring, cleanup, power control, diagnostics, and maintenance. This final release focuses on polish, export workflows, and release packaging stability.

### Highlights
- Modern modular dashboard with quick actions and glass styling
- Rounded modular panels with persistent glass appearance preferences
- Safe cleanup and protected user data handling
- Power scheduling and shutdown timer controls
- Network diagnostics and system snapshot reporting
- Activity log and system report export
- Adjustable Windows acrylic backdrop strength

### Usage
1. Install the virtual environment dependencies
2. Run the app with `python main.py`
3. Generate an EXE with `python build_exe.py`
4. Build an installer with `python build_installer.py` on a Windows machine with Inno Setup installed

### Safety notes
- Destructive operations require explicit confirmation.
- User directories and critical Windows system folders remain protected.
- System-affecting features are deliberately narrow and user-controlled.

### Known deployment note
- EXE and installer creation are validated through the build scripts and are intended for Windows runtime execution.
- The installer step requires Inno Setup 6 (`iscc.exe`) on the target machine.
