# Sync Viewport
Sync View Version 1.0.1:
* Can selectively sync viewports together
    * Only the view is synced, everything else can be configured independently as usual
        * i.e. two viewports can be sync where one displays wireframe while the other displays material preview
* Thee sync modes for viewports with sync enabled:
    * Sync all viewports in the same window
    * Sync all viewports in the same workspace (works across windows)
    * Sync all viewports in the blend file
* Performance Toggles:
    * Pause sync on all viewports
    * Pause sync during playback
    * Don't sync viewports in camera view

Known Minor Issue:
If a viewport is syncing and it enters quad view, all quad view settings will be set to false. 
