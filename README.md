# Sync Viewport
Inspired by ZBrush's thumbnail view, which can shows a synced silhouette view of your sculpt as your work, this addon aims to provide a similar functionality to Blender.

With Sync Viewport installed, you can choose what viewports you want to sync together via a toggle-able button in the header region. The addon also offers 3 different modes of syncing: 
1. Sync only viewports in the same window
2. Sync only viewports in the same workspace (also syncs other open windows with a 3d viewport)
3. Sync all viewports in the blend file, which will work across workspaces

If your machine isn't powerful enough to run the addon and maintain stable performance, there are also options to turn off syncs:
1. Turn off sync temporarily
2. Turn off sync when playing an animation
3. Turn off sync for viewports in camera view.


### TLDR:
Sync View Version 1.0.2:
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
