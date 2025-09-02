# Project Description: CIA Website

This document provides a concise overview of the CIA project to quickly bring a new AI assistant up to speed. This code was used in collaboration with Take Action Tuscon.

## Project Overview

*   **Project Type:** Static Website
*   **Technology:** [Hugo](https://gohugo.io/)
*   **Purpose:** This is the official website for the "Collective Improvement Association" a pro-democracy activism hub. The site serves to inform visitors about events, provide contact information, and showcase the group's activities.

## Technology Stack

*   **Framework:** Hugo is the static site generator.
*   **Templating:** Hugo's Go-based templating engine is used for all layouts.
*   **Styling:** Primarily custom CSS, with some Bootstrap utilities. The main stylesheet is located at `themes/mcp-theme/assets/css/main.css`.
*   **Scripting:** The `scripts/` directory contains Python and shell scripts used for managing and updating the events calendar from a CSV file.

## Key Project Structure

The most important files and directories are located within the `themes/mcp-theme/` directory, which is the active theme for the site.

*   `themes/mcp-theme/layouts/_default/baseof.html`: This is the master template that defines the HTML structure for every page on the site. It includes the header and footer partials.
*   `themes/mcp-theme/layouts/partials/`: This directory contains reusable HTML components.
    *   `header.html`: The original site header.
    *   `header-new.html`: The new, recently developed header that is currently active.
    *   `footer.html`: The site footer.
*   `themes/mcp-theme/assets/css/main.css`: The primary stylesheet for the entire website. All new styles should be added here.
*   `content/`: This directory holds the Markdown content for the various sections of the website (e.g., `about/`, `calendar/`).
*   `layouts/`: This directory at the root is used for overriding theme layouts. Currently, it contains top-level page layouts and our temporary `header-skeleton.html` file that was used for development.
*   `static/`: Contains all static assets, including images, fonts, and icons.

## Recent Development & Current State

The most recent major change was a complete replacement of the site-wide header. The new header is now live and the old development files have been removed. All styles for the new header have been moved to `themes/mcp-theme/assets/css/main.css` and are scoped under the `header.header-new` class to prevent conflicts.

*   **Old Header:** The original header is defined in `themes/mcp-theme/layouts/partials/header.html`.
*   **New Header:** The new header was developed in `layouts/section/header-skeleton.html` and has been moved to its permanent, testable location at `themes/mcp-theme/layouts/partials/header-new.html`.
*   **Activation:** The new header is currently active because `baseof.html` has been modified to point to `header-new.html`.
*   **Styling:** All styles for the new header have been moved to `themes/mcp-theme/assets/css/main.css` and are scoped under the `.header-new` class to prevent conflicts.

The immediate next step is to confirm the new header is working as expected and then proceed with cleanup by replacing the old header file with the new one and deleting the temporary development files. 