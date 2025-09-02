# Take Action Tucson Website

A Hugo-based website for Take Action Tucson, providing a central hub for local activism events and resources.

## Features

- Responsive design with Bootstrap
- Real Google Calendar integration with automatic event updates
- Printable event calendar for distribution
- Protest sign gallery
- Contact form
- Custom color scheme matching Take Action Tucson branding

## Quick Start

### Prerequisites

- [Hugo](https://gohugo.io/getting-started/installing/) (Extended version 0.110.0 or higher recommended)
- [Git](https://git-scm.com/downloads)

### Running Locally

1. Clone this repository:
   ```bash
   git clone <repo-url>
   cd take-action-tucson-site
   ```

2. The following images are needed in the `static/images/` directory:
   - `protest-statue.jpg`
   - `protest-books.jpg`

3. Start the Hugo development server:
   ```bash
   bash run.sh
   ```
   This script will check for dependencies and start the server.

4. Open your browser and navigate to http://localhost:1313

## Project Structure

- `content/`: Markdown files for site content
- `layouts/`: HTML templates for the site
- `static/`: Static assets like images, CSS, and JavaScript
- `themes/mcp-theme/`: Custom theme files
- `scripts/`: Scripts for calendar management. See `scripts/README.md` for more.
- `vercel.json`: Configuration for Vercel deployment.

## Calendar Integration

The site uses a real Take Action Tucson Google Calendar.

- Calendar ID: `f81dd042d9553c506027f96a0335662281bfcb7c772ee33f7f5629f6294779e3@group.calendar.google.com`

Events can be added to the Google Calendar using the Google Calendar web interface or the tools in the `scripts` directory.

## Deployment

This site is continuously deployed to Vercel when changes are pushed to the main branch.

The live site can be viewed at a Vercel URL, which you can find in your Vercel project dashboard.

The `vercel.json` file in the repository specifies the Hugo version to be used for the build.

## License

This project is licensed under the **Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0)**. You can view the full license text in the [LICENSE](LICENSE) file.

**What this means:**

*   **You are free to:**
    *   **Share:** Copy and redistribute the material in any medium or format.
    *   **Adapt:** Remix, transform, and build upon the material.
*   **Under the following terms:**
    *   **Attribution:** You must give appropriate credit.
    *   **NonCommercial:** You may not use the material for commercial purposes.
    *   **ShareAlike:** If you remix, transform, or build upon the material, you must distribute your contributions under the same license as the original.

#### Commercial Licensing

We use a dual-licensing model. If you are a for-profit entity and wish to use this software for commercial purposes, please contact us at **contact@takeactiontucson.org** to arrange for a commercial license.

### Development

The primary tools for managing the calendar are located in the `/scripts` directory. See the README in that directory for more information on the Python-based import and editing tools.
