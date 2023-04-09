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


## Syncing Viewports in the same window

https://user-images.githubusercontent.com/57331630/230760376-cbddfac8-4525-430b-9dcd-80f7ec0b40ab.mp4


## Syncing Viewports in the same workspace

https://user-images.githubusercontent.com/57331630/230760556-eb94e3b8-ca40-443d-8523-286e3c922c6e.mp4




Known Minor Issue:
If a viewport is syncing and it enters quad view, all quad view settings will be set to false. 
