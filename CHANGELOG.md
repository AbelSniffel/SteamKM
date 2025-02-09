0.8.0-beta (In Development) # Skipping 0.7.0
Security & Encryption:
+ Implemented SHA-256 encryption for Steam Keys file
+ Added GUI option to change encryption password

Backups & Data Management:
+ More options for Steam Key data backups
+ More options for importing Steam Key data
+ New unified auto correction system for adding games & file importing (TXT)
* Potentially improved speed of adding large numbers of games

UI/UX Improvements:
+ Added 2 new themes called "Ocean" and "Forest"
+ Added search bar to Theme Customization Menu
+ Added customizable grouped elements background color
+ Added customizable changelog background color
+ Added Discord spoiler style copy option
+ Added selected branch name to "No updates available" message
+ Added a new message "Restart required" after downloading update
+ Improved visuals for Game Table/List
+ Real-time status message updates for Update Menu and Main GUI
+ Version selector combobox width is controlled by the branch
+ Dynamic text for download button, changing based on selected version
+ Dynamic "Show/Hide" text for Toggle All Keys
+ Dynamic hover color for comboboxes
+ Grouped theme customization elements together
+ Grouped category customization elements together
+ Combobox dropdown color is now themed
* Reorganized color customization groups
* Tweaked the default themes a bit
* Slightly rounder default corners
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
* Fixed scrollbar corner visual bug

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
+ Scroll wheel rejection for the Edit Menu, scroll with confidence without accidentally changing game categories
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
