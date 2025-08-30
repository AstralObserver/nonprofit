# Take Action Tucson Website - Code Review Checklist

This checklist helps ensure code quality, maintainability, and consistency across the TATwebsite project.

## 🤖 AI-Assisted Checks

These items can be efficiently reviewed by AI tools:

### Code Quality & Standards
- [ ] **Hugo templating syntax** - Proper Go template syntax and best practices
- [ ] **CSS organization** - All styles properly scoped under appropriate classes
- [ ] **Bootstrap utilization** - Use Bootstrap classes instead of custom CSS wherever possible
- [ ] **CSS minimization** - Custom CSS kept to absolute minimum (branding, unique components only)
- [ ] **File structure** - Files placed in correct directories per Hugo conventions
- [ ] **Naming conventions** - Consistent naming for files, classes, and variables
- [ ] **Code duplication** - No unnecessary repetition of code blocks
- [ ] **Performance** - Efficient CSS selectors and minimal resource loading
- [ ] **Unused dependencies** - Remove unused CSS/JS libraries (e.g., Font Awesome if not used)

### Bootstrap Best Practices
- [ ] **Spacing utilities** - Use Bootstrap spacing classes (`mt-*`, `mb-*`, `p-*`) instead of custom margins/padding
- [ ] **Layout system** - Leverage Bootstrap grid and flexbox utilities (`d-flex`, `justify-content-*`, etc.)
- [ ] **Typography** - Use Bootstrap typography classes (`h1-h6`, `text-*`, `fw-*`) where applicable
- [ ] **Responsive design** - Use Bootstrap responsive utilities (`d-md-none`, `col-lg-*`) instead of custom media queries
- [ ] **Component classes** - Use Bootstrap components (buttons, cards, forms) as base, customize minimally

### Security & Best Practices
- [ ] **XSS prevention** - Proper escaping in templates (`{{ . | safeHTML }}` usage)
- [ ] **External links** - `rel="noopener noreferrer"` on external links
- [ ] **Image optimization** - Appropriate image formats and sizes
- [ ] **Accessibility basics** - Alt text, semantic HTML, ARIA labels

### Documentation & Comments
- [ ] **Code comments** - Complex logic explained
- [ ] **README updates** - Documentation reflects any new features/changes
- [ ] **TODO items** - New TODOs added to `TODO.md` if applicable

## 👤 Human Review Required

These items require human judgment and domain knowledge:

### Content & UX
- [ ] **Content accuracy** - Event details, contact information, messaging
- [ ] **Visual design** - Layout, colors match Take Action Tucson branding
- [ ] **User experience** - Navigation flows logically, mobile responsiveness
- [ ] **Accessibility compliance** - Screen reader compatibility, keyboard navigation

### Functionality
- [ ] **Calendar integration** - Events display correctly from Google Calendar
- [ ] **Cross-browser testing** - Works in major browsers (Chrome, Firefox, Safari, Edge)
- [ ] **Mobile testing** - Responsive design functions on various screen sizes
- [ ] **Print functionality** - Print calendar renders properly

### Business Logic
- [ ] **Event data handling** - Proper merging of manual and calendar events
- [ ] **Organizer information** - Multiple organizers handled correctly
- [ ] **Image management** - Event images display and scale appropriately

## 📋 Specific Areas to Review

### Theme Files (`themes/mcp-theme/`)
- [ ] **Header consistency** - `header-new.html` vs `header.html` usage
- [ ] **CSS scoping** - All new styles under `.header-new` or appropriate classes
- [ ] **Template inheritance** - Proper use of `baseof.html` structure
- [ ] **Bootstrap integration** - Templates use Bootstrap classes extensively

### CSS Files (`themes/mcp-theme/assets/css/`)
- [ ] **Custom CSS minimized** - Only branding colors, fonts, and truly unique styles
- [ ] **Bootstrap override strategy** - Use CSS custom properties for theme colors
- [ ] **Unused styles removed** - No dead CSS code
- [ ] **Dependency cleanup** - Remove unused external CSS libraries

### Scripts (`scripts/`)
- [ ] **Python dependencies** - `requirements.txt` up to date
- [ ] **Error handling** - Scripts handle missing files/network issues gracefully
- [ ] **Calendar sync** - Import/export functionality works correctly

### Static Assets (`static/`)
- [ ] **Image optimization** - Files not unnecessarily large
- [ ] **Icon consistency** - Favicon and touch icons present and correct

## 🔄 Pre-Deployment Checklist

- [ ] **Local testing** - `hugo server -D` runs without errors
- [ ] **Build verification** - `hugo` builds successfully
- [ ] **Calendar update** - Run `./scripts/update-calendar.sh` if events changed
- [ ] **Git status clean** - No unintended files committed
- [ ] **CSS size check** - Custom CSS file size minimized
- [ ] **Bootstrap utilization** - Maximum use of Bootstrap utilities achieved

## 📝 Review Notes Template

```
## Review Summary
**Reviewer:** [Name]
**Date:** [YYYY-MM-DD]
**Branch/Commit:** [hash]

### Changes Reviewed
- [ ] [Brief description of changes]

### Bootstrap Utilization
- [ ] [Areas where Bootstrap was used instead of custom CSS]
- [ ] [Remaining custom CSS justified]

### Issues Found
- [ ] [Issue 1 - severity level]
- [ ] [Issue 2 - severity level]

### Recommendations
- [Any suggestions for improvement]
- [Bootstrap classes that could replace custom CSS]

### Approval Status
- [ ] ✅ Approved - Ready to merge
- [ ] ⚠️ Approved with minor issues
- [ ] ❌ Needs changes before approval
```

## 🛠️ Tools & Commands

### AI Review Commands
```bash
# Check Hugo syntax
hugo --gc --minify --cleanDestinationDir

# Validate HTML (if htmlproofer installed)
htmlproofer public/ --check-html --check-external-hash

# CSS validation
npx stylelint "themes/mcp-theme/assets/css/*.css"

# Check CSS file size
wc -l themes/mcp-theme/assets/css/main.css
```

### Manual Testing
```bash
# Start local server
./run.sh

# Update calendar
./scripts/update-calendar.sh

# Test event editor
cd scripts && python event_editor_gui.py
```

## 🎯 Bootstrap-First Development Philosophy

**Before writing custom CSS, ask:**
1. Does Bootstrap have a utility class for this?
2. Can I achieve this with Bootstrap's grid system?
3. Is this truly unique to our brand/design?

**Keep custom CSS only for:**
- Brand colors (CSS custom properties)
- Custom fonts
- Truly unique component designs
- Print styles
- Complex animations/interactions

**Target:** Keep `main.css` under 50 lines of actual styles (excluding comments/whitespace).