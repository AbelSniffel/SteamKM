0.7.0-beta (Upcoming Update - Still in development)
Security & Encryption:
+ Implemented SHA-256 encryption for Steam Keys file
+ Added GUI option to change encryption password

Backups & Data Management:
* More options for Steam Key data backups
* More options for importing Steam Key data
* Potentially improved speed of adding large numbers of games
* Improved and fixed TXT file importing

UI/UX Improvements:
+ Added search bar to Theme Customization Menu
+ Added group box color customization
+ Added selected branch name to "No updates available" message
+ Dynamic text for download button, changing based on selected version
+ Dynamic "Show/Hide" text for Toggle All Keys
+ Dynamic hover color for comboboxes
+ Unified Theme Customization elements within a single border
+ Real-time updates for "Update Available" text in Update Menu
* Improved Update menu
* Halved corner radius for items inside border groups
* Slightly rounder default corner radius
* Fixed scrollbar corner visual bug
* Disabled editing/removing the "New" category
- Removed redundant "(latest)" text
- Removed combobox hover/dropdown background customization
- Removed restart script (exploring alternatives for future)

0.6.0-beta
+ New Moveable Function Dock which houses various buttons
+ Categories menu (able to add, edit or remove categories)
+ Added a slider for controlling the interactables border size
+ Support for importing txt files
+ New indicator number inside the Edit menu
+ Added the text "Checking for Updates" to the main GUI
+ Icons are theme sensitive (controlled by the text color)
+ Dynamic "hover" and "pressed" state colors for buttons
* Update Available text is now branch sensitive
* Slight improvements to the Search bar
* Made the text "(latest)" be permanently attached to newest available version
* Made the boxes inside the Edit menu stick to the top
* Edit menu boxes now have a fixed vertical size
* Halved the drop-down menu border radius
* Reorganized Customization menu
* Some other small changes and bug fixes
- Removed Github token requirement for Alpha Builds
- Removed customizable button hover and pressed colors

0.5.1-beta
+ Added version selector to choose which version to install
+ Added download time estimation
+ Added download cancellation button
+ Added popup which opens after a successful update
+ New automatic update checker which doesn't freeze the GUI
+ Scroll wheel rejection for the Edit Menu, scroll with confidence without accidentally changing game categories
* Tweaked the color customization menu style
* Tweaked the default themes a bit
* Changed the size of the checkboxes
* Changed the Update menu layout
- Removed Rich Text support from Add games field, this resolves 
styling issues that appear when copying from stylized places (like websites)
- Removed text "Game 1, Game 2, etc." from the Edit menu

0.4.5-beta
+ Added themed download bar
* Tweaked the GUI a bit

0.4.4-beta
+ Added Update menu
- Removed Automatic Update Checking for now

0.4.0-beta
* Fixed Updater
