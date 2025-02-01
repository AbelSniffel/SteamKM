Future problems/ideas
~ Need to dynamically calculate the game table grid
~ Need to make dynamic color take into account how much brighter or darker hover and pressed colors have to get and if those calculated colors will hit pure white or black value (aka it hits the cap before it actually gets to it's "appropriate" color), which means that the color difference between the 3 states (just the color, hover and pressed) is too low.
~ Need to make the buttons height lower for other elements which are not part of the main window (like popup messages: Change password)
~ Need to fix the starting progress bar chunck to be appropriately rounded and not a square (Need to check if it's fixed now)
~ Need to somehow remove the drop shadow behind stuff like QComboBox and QMenu
~ Add caching for the update part (automatic update should cache the info for the Update menu) - CURRENTLY WORKING ON IT
~ Maybe add little icon for default themes selection which lights up to indicate the selected theme 
(Dark,Light,Forest,Ocean - all icons are perfectly connected and flow into each other)


0.7.0-beta (Upcoming Update - Still in development)
Security & Encryption:
+ Implemented SHA-256 encryption for Steam Keys file
+ Added GUI option to change encryption password

Backups & Data Management:
* More options for Steam Key data backups
* More options for importing Steam Key data
* Potentially improved speed of adding large numbers of games
* Improved TXT file import

UI/UX Improvements:
+ Added 2 new themes called "Ocean" and "Forest"
+ Added search bar to Theme Customization Menu
+ Added customizable grouped elements background color
+ Added customizable changelog background color
+ Improved visuals for Game Table/List
+ Added selected branch name to "No updates available" message
+ Dynamic text for download button, changing based on selected version
+ Dynamic "Show/Hide" text for Toggle All Keys
+ Dynamic hover color for comboboxes
+ Grouped theme customization elements together
+ Grouped category customization elements together
+ Real-time updates for "Update Available" text in Update Menu
* Changed the Dark Mode checkbox into a dropdown menu
* Game Table corner button is now affected by button color
* Tweaked the default themes a bit
* Reorganized color customization groups
* Encased categories into a group (Manage Categories menu)
* Halved corner radius for items inside border groups
* Slightly rounder default corners
* Disabled editing & removal for the "New" category

Bug Fixes:
* Fixed scrollbar corner visual bug

Removals:
- Removed "(latest)" text
- Removed combobox hover & dropdown background customization
- Removed combobox dropdown menu border
- Removed restart script (exploring alternatives for future)

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
* Some other small changes and bug fixes

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
