2.0.0-beta
(SteamAPI and UI Overhaul)
* Probably missed a couple things that I changed but oh well, here are the ones that I remember:

Data Management: 
+ Added options for importing and exporting manager settings file
+ Able to open the folder location using the new "Open Folder Location" button (Settings Menu)
* Game keys file and manager settings files have been moved to "%APPDATA%\Roaming\SteamKM" or "~/.config/SteamKM" (Linux/macOS)
+ Implemented a migration script, which will move all files from the old location to the new one (%APPDATA%)

Steam Integration:
+ Implemented Steam API for automatic game data retrieval
+ Added comprehensive game metadata: AppIDs, icons, and user reviews
+ Introduced editable AppID field with image preview in Edit Menu
+ Enhanced game management with real-time Steam data fetching
+ Integrated browser launch capability for selected games
+ Implemented intelligent image retrieval during file imports
+ Added streamlined workflow for fetching data for new game entries

Update Improvements:
+ Implemented caching for version information
+ Added automatic update checking checkbox
+ Updates are now downloaded to the OS specific TEMP folder
+ Optimized update notification system for better feedback
+ Integrated update status information into Main UI
+ Changelog remembers where it was scrolled to and is no longer affected by branch changes
+ Made the Update available text show the new version number and made the text be clickable
+ Updates are now downloaded to the OS temporary folder instead of the executable location
+ Added a new refresh changelog button to the Update menu
* Changed the Update menu icon
* Made the progress bar start from 4%, which is wide enough to have rounded corners

Encryption Improvements:
+ Extended theming to encryption-related interfaces
* Improved the encryption password changing interface

UI/UX Improvements:
+ Brand new redesigned UI with enhanced functionality
+ Implemented automatic saving when closing menus
+ New Settings Menu was added to the Main UI (Cog Icon), replaces the hamburger menu
+ Added 2 more copy options "Title Only" and "Key Only"
* Added tooltips for specific buttons
+ Enhanced changelog readability with the addition of a scrollbar
+ Added a color customizable arrow for all combo boxes
+ Implemented sortable columns with header-click functionality
+ Added an alternative layout option for switching search bar row location
+ Added all game adding and backup related options into the new "+" icon menu button
* Changed the "Add Games" button into a "+" icon and moved it to the top bar
* Improved the speed of the hide and show keys function
* Moved change password button to the new Settings Menu
* Selected cell now selects the entire row instead of a single cell
* Right click menu and button shaped menus (QMenu) now use group box background color
* Improved notification system for all user actions
* Streamlined message dialogs and right-click menu organization
* Reduced the Button height from 32px to 30px
* New minimum and maximum limits for a couple of Theme sliders
* Scrollbar slider names have been changed to better reflect what they control
* Updated PySide6 to version 6.9.0

Theme System Enhancements:
+ New custom Color Customization menu to replace the OS specific menu
+ Real-time UI color updates
+ Added "Fire" theme to complement existing options
+ Implemented theme quick-switcher for the Theme Menu
+ Added custom sliders for element size controls
+ Introduced unified styling options as an alternative appearance
+ Implemented dynamic scrollbar height for specific elements
+ Refined default themes with improved visuals
+ Enhanced element grouping with improved corner rounding
+ Standardized input field styling across the application

Bug Fixes:
* Corrected typo in game removal confirmation message
* Resolved performance degradation in Theme Menu sliders (when continually reopening the Theme Menu)
* Fixed update branch selection inconsistencies
* Fixed vertical gaps between elements in Theme Menu when using the search bar

Removals:
- Removed function dock in favor of improved layout
- Removed "Apply and Save" button from Theme menu
- Removed "Save", "Cancel" buttons from Category menu
- Removed number indexes from the Category Menu and Edit Games Menu
- Removed built-in color customization menu
- Removed interactable border size related code
  
___
0.8.0-beta
Security & Encryption:
+ Implemented SHA-256 encryption for Steam Keys file
+ Added GUI option to change encryption password

Backups & Data Management:
+ More options for Steam keys data backups
+ More options for importing Steam keys data
+ New auto correction system for adding games & file importing (TXT)

UI/UX Improvements:
+ Added 2 new themes called "Ocean" and "Forest"
+ Added search bar to Theme Customization Menu
+ Added customizable grouped elements background color
+ Added customizable changelog background color
+ Added Discord spoiler style copy option
+ Added selected branch name to "No updates available" message
+ Added a new message "Restart required" after downloading update
+ Added confirmation message when trying to close Update Menu with an active download
+ Improved visuals for Game Table/List
+ Real-time status message updates for Update Menu and Main GUI
+ Version selector combobox width is controlled by the branch
+ Dynamic text for download button, changing based on selected version
+ Dynamic "Show/Hide" text for Toggle All Keys
+ Dynamic hover color for comboboxes
+ Grouped theme customization elements together
+ Grouped category customization elements together
+ Combobox dropdown color is now themed
+ Added more default category options
+ Added scroll wheel rejection for the Theme Customization Menu sliders
* Changed most of the color names to make it easier to search
* Reorganized color customization groups
* Tweaked the default themes a bit
* Slightly rounder default corners
* Progress bar radius is now controlled by Corner Radius
* Changed the Dark Mode checkbox into a dropdown menu
* Created a gap between the combobox and it's dropdown menu
* Game Table corner button is now affected by button color
* Encased categories into a group (Manage Categories menu)
* Halved corner radius for items inside border groups
* Changed the default dock position to be on the top
* Increased scrollbar customization range
* Disabled editing & removal for the "New" category
* Changed Stable branch into Release branch

Bug Fixes:
* Finally fixed scrollbar corner visual bug
* In progress download will now stop when closing Update Menu

Removals:
- Removed "(latest)" text
- Removed combobox hover & dropdown background customization
- Removed combobox dropdown menu border
- Removed restart script (exploring alternatives for future)
- Removed Alpha branch as I don't plan to use it for releases

___
0.6.0-beta
Data Management:
+ Added support for importing txt files

UI/UX Improvements:
+ New Moveable Function Dock which houses various buttons
+ Categories menu (able to add, edit or remove categories)
+ Added a slider for controlling the interactables border size
+ New indicator number inside the Edit menu
+ Added the text "Checking for Updates" to the main GUI
+ Icons are theme sensitive (controlled by the text color)
+ Dynamic "hover" and "pressed" state colors for buttons
+ Update Available text is now branch sensitive
* Slight improvements to the Search bar
* Made the text "(latest)" be permanently attached to newest available version
* Made the boxes inside the Edit menu stick to the top
* Edit menu boxes now have a fixed vertical size
* Halved the drop-down menu border radius
* Reorganized Customization menu
* Some other small changes

Bug Fixes:
* I don't remember which bugs :/

Removals:
- Removed Github token requirement for Alpha Builds
- Removed customizable button hover and pressed colors

___
0.5.1-beta
UI/UX Improvements:
+ Added version selector to choose which version to install
+ Added download time estimation
+ Added download cancellation button
+ New automatic update checker which doesn't freeze the GUI
+ Added a popup which opens after a successful update
+ Added Scroll wheel rejection for the Edit Menu, scroll with confidence without accidentally changing game categories
* Tweaked the color customization menu style
* Tweaked the default themes a bit
* Changed the size of the checkboxes
* Changed the Update menu layout

Removals:
- Removed Rich Text support from Add games field, this resolves styling issues that appear when copying from stylized places (like websites)
- Removed text "Game 1, Game 2, etc." from the Edit menu

___
0.4.5-beta
UI/UX Improvements:
+ Added themed download bar
* Tweaked the GUI a bit

___
0.4.4-beta
UI/UX Improvements:
+ Added Update menu
- Removed Automatic Update Checking for now

___
0.4.0-beta
Bug Fixes:
* Fixed Updater
