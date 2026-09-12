---
name: pc-control
description: Automate Windows PC tasks, window management, mouse clicks, and keyboard actions.
---

# PC Control & Desktop Automation Skill

## Capabilities
- Launch foreground applications and web destinations (`applications` tool).
- Manage active windows: list, focus, minimize, maximize, restore, or close (`window_manager` tool).
- Type text, press navigation keys, and invoke shortcuts like `ctrl+c`, `win+d` (`keyboard` tool).
- Mouse interaction: click coordinates, click UI elements, scroll up/down (`computer` tool).
- Screen observation: inspect active UI tree and take screenshots (`screen_observer` tool).

## Workflow Guidelines
1. To open an app or search, use `applications` to guarantee visible foreground launching.
2. To interact with an open window, focus it first with `window_manager` then send keystrokes with `keyboard`.
3. To inspect UI elements, use `observe_screen` to get element IDs (`e1`, `e2`) before clicking.
