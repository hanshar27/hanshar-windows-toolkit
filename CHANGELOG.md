# Changelog

## Unreleased

### Added
- Renamed the packaged executable, installer, release bundle, and PyInstaller spec to use the Hanshar name while preserving existing per-user data locations
- System Information page with complete MSInfo32 and DxDiag reports, local report files, and background generation
- Confirmed standby-memory cache purge in Windows Maintenance
- Fixed glass-style appearance based on the provided dashboard reference, with adjustable Windows acrylic backdrop
- Storage Cleaner support for `%TEMP%`, Windows Temp, Prefetch, and the Recycle Bin; Recycle Bin is opt-in and emptied through the Windows Shell API after confirmation

### Changed
- Updated visible product branding to Hanshar Windows Toolkit while retaining existing persistent data locations
- Save packaged application preferences to persistent per-user settings storage
- Reworked the sidebar into flat icon navigation and redesigned the dashboard as a warm-charcoal Bento grid with live CPU/RAM gauges and performance history
- Increased dashboard and sidebar typography for improved readability
- Matched the System Overview and Quick Actions card backgrounds to the other dashboard cards to prevent excessive transparency
- Kept acrylic backdrop pixels opaque to pointer hit-testing so clicks on the application background remain interactive
- Read friendly CPU, Windows edition, and GPU names from Windows CIM instead of generic platform identifiers or an optional WMI package
- Reported disk capacity for the drive where the application is running
- Added GPU temperature reading through NVIDIA `nvidia-smi` with LibreHardwareMonitor/OpenHardwareMonitor fallback
- Changed the dashboard temperature card from CPU temperature to GPU temperature; it remains temperature-only when no GPU sensor is available
- Read NVIDIA GPU temperature directly from `nvidia-smi` with a live sensor check; this machine reports 55.0 C for its GTX 1080
- Replaced the System Monitor CPU Temperature line with GPU Temperature and included it in the system snapshot
- Made dashboard metric titles, values, and descriptions wrap to available card width, and tightened Quick Action labels for smaller windows
- Made Storage Cleaner vertically scrollable and constrained the category, preview, and log sections so Scan preview stays accessible in smaller windows
- Protected PyInstaller `_MEI` runtime folders from Temp scans and cleanup so the running application retains `base_library.zip`

### Fixed
- Persisted System Information reports outside the temporary PyInstaller extraction directory
- Removed the previous selectable themes and applied rounded glass-style panels across the feature pages
- Removed an unsupported CustomTkinter `bg_color` option that caused a startup crash
- Prevented theme startup crashes by limiting configuration to options supported by each widget

## 1.1.0 - 2026-11-16

### Added
- Premium dashboard workflow with quick actions for exports and report generation
- Final release polish across status, footer, and desktop shell behavior
- More robust packaging CLI for EXE bundling and installer generation
- Expanded project documentation and release notes for deployment readiness

### Improved
- Replaced the previous appearance choices with the glass styling used by the current dashboard
- Packaging scripts for cleaner Windows release workflows
- User-facing polish for dashboard summaries and export actions

### Fixed
- Theme selection edge cases and invalid value handling
- Release builder arguments for more predictable Windows packaging
- Stability of project-level validation during final polish passes

## 1.0.0 - 2026-11-16

### Added
- Modular Windows utility desktop app shell with sidebar navigation
- Dashboard with live system information
- Storage cleaner with protected safe scan logic
- Power manager and shutdown timer
- Network tools for diagnostics
- System monitor panel with snapshot health data
- Gaming and maintenance panels
- Settings with glass intensity and startup persistence
- Windows EXE and installer build support
- Branded icon and release polish

### Improved
- Safety checks for destructive cleanup actions
- Startup registry integration for Windows auto-launch
- Config persistence and application footer/status UI

### Fixed
- Protected path logic and testability of storage manager
- Safe command execution patterns for Windows tools
- Packaging path handling for config file
