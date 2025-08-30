document.addEventListener('DOMContentLoaded', function() {
    // --- Constants for configuration ---
    const MOBILE_RESIZE_CONFIG = {
        maxSize: 2.0,                  // Maximum font size in rem
        minSize: 1.0,                  // Minimum font size in rem
        enableHyphenationThreshold: 1.2, // Font size at which to enable CSS hyphenation
        longWordThreshold: 12,         // Character count to consider a word "long"
        avgCharWidth: 12,              // Estimated average character width in pixels at 1rem
        containerWidthFactor: 0.9      // Percentage of container width to use for calculations
    };

    const DESKTOP_RESIZE_CONFIG = {
        maxSize: 1.8,
        minSize: 1.2,
        enableHyphenationThreshold: 1.3,
        longWordThreshold: 18,
        avgCharWidth: 14,
        containerWidthFactor: 0.9
    };
    
    const RESIZE_DEBOUNCE_DELAY = 250; // Delay in ms to wait before re-running resize logic

    /**
     * Hides events that have already ended based on Arizona time.
     * This runs once on page load to clean up the pre-rendered list.
     */
    function hidePastEvents() {
        // Use the current UTC-based timestamp. Since each event end time
        // includes the explicit "-07:00" offset for Arizona, simply
        // comparing their absolute timestamps is sufficient and avoids
        // browser-specific timezone parsing issues.
        const now = new Date();
        const eventElements = document.querySelectorAll('[data-end-datetime]');

        eventElements.forEach(el => {
            const endDateTimeStr = el.dataset.endDatetime;
            if (!endDateTimeStr) {
                return; // Don't hide events if we can't determine their end time.
            }

            try {
                const eventEndDate = new Date(endDateTimeStr);
                // Check if the date is valid before comparing
                if (!isNaN(eventEndDate.getTime()) && eventEndDate < now) {
                    el.style.display = 'none';
                }
            } catch (e) {
                console.error("Could not parse event date:", endDateTimeStr, e);
            }
        });
    }

    // Run the function to hide events that have already passed today.
    hidePastEvents();

    /**
     * Intelligent text resizing for long event titles
     * Reduces font size before enabling hyphenation
     */
    function adjustEventTitleSizes() {
        // Handle mobile event titles
        const mobileTitles = document.querySelectorAll('.event-banner-title');
        mobileTitles.forEach(title => {
            adjustTitleSize(title, MOBILE_RESIZE_CONFIG, true);
        });

        // Handle desktop event titles
        const desktopTitles = document.querySelectorAll('.event-info .event-title');
        desktopTitles.forEach(title => {
            adjustTitleSize(title, DESKTOP_RESIZE_CONFIG, false);
        });
    }

    function adjustTitleSize(element, config, isMobile) {
        const { maxSize, minSize, enableHyphenationThreshold, longWordThreshold, avgCharWidth, containerWidthFactor } = config;
        
        // Reset styles
        element.style.fontSize = maxSize + 'rem';
        element.style.hyphens = 'none';
        
        const container = element.parentElement;
        const containerWidth = container.offsetWidth;
        const words = element.textContent.split(/\s+/);
        
        // Find the longest individual word
        const longestWord = words.reduce((longest, word) => 
            word.length > longest.length ? word : longest, '');
        
        let fontSize = maxSize;
        const availableWidth = containerWidth * containerWidthFactor;
        
        const estimatedWordWidth = longestWord.length * avgCharWidth * fontSize;

        if (estimatedWordWidth > availableWidth && longestWord.length > longWordThreshold) {
            const targetFontSize = (availableWidth / (longestWord.length * avgCharWidth));
            fontSize = Math.max(minSize, Math.min(maxSize, targetFontSize));
            element.style.fontSize = fontSize + 'rem';
        }
        
        // If we've reached minimum size and longest word is still very long, enable hyphenation
        if (fontSize <= enableHyphenationThreshold && longestWord.length > 20) {
            element.style.hyphens = 'auto';
        }
    }

    // Run title adjustment on load
    adjustEventTitleSizes();

    // Re-run on window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            adjustEventTitleSizes();
            reCheckAndInitialize();
        }, RESIZE_DEBOUNCE_DELAY);
    });

    // Handle button clicks for TYPE filtering
    const filterContainer = document.getElementById('calendar-type-nav');
    if (filterContainer) {
        filterContainer.addEventListener('click', function(event) {
            if (event.target.tagName === 'BUTTON') {
                const filter = event.target.dataset.filter;
                filterAndRenderEvents(filter);
            }
        });
    }

    // Handle button class toggling for all groups
    document.querySelectorAll('.btn-group').forEach(group => {
        group.addEventListener('click', function(event) {
            if (event.target.tagName === 'BUTTON') {
                const buttons = this.querySelectorAll('button');
                buttons.forEach(button => {
                    button.classList.remove('btn-primary');
                    button.classList.add('btn-outline-primary');
                });
                event.target.classList.remove('btn-outline-primary');
                event.target.classList.add('btn-primary');
            }
        });
    });

    // Lightbox logic
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');

    function openLightbox(src) {
        if (src) {
            lightboxImg.src = src;
            lightbox.style.display = 'flex';
        }
    }

    function closeLightbox() {
        lightbox.style.display = 'none';
        lightboxImg.src = '';
    }

    document.querySelector('body').addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('event-photo')) {
            const lightboxSrc = e.target.dataset.lightboxSrc || e.target.src;
            openLightbox(lightboxSrc);
        }
    });

    lightbox.addEventListener('click', () => {
        closeLightbox();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeLightbox();
        }
    });

    function filterAndRenderEvents(filter) {
        const desktopEvents = document.querySelectorAll('#desktop-events-list .event-list-item');
        const mobileEvents = document.querySelectorAll('#mobile-events-list .event-card-wrapper');
        
        const allEventElements = [...desktopEvents, ...mobileEvents];

        allEventElements.forEach(el => {
            const eventTypes = el.dataset.eventTypes || '';
            if (filter === 'all' || eventTypes.includes(filter)) {
                el.classList.remove('hidden');
            } else {
                el.classList.add('hidden');
            }
        });

        // After filtering, re-run the check for past events to ensure
        // that newly visible 'all' events are correctly hidden if they are in the past.
        hidePastEvents();
        
        // Re-adjust title sizes for newly visible events
        setTimeout(() => {
            adjustEventTitleSizes();
            reCheckAndInitialize();
        }, 50);
    }

    /**
     * Checks if event descriptions are overflowing and applies a class to enable
     * the fadeout effect only when necessary.
     */
    function checkDescriptionOverflow() {
        // Check desktop events
        const desktopEventItems = document.querySelectorAll('#desktop-events-list .event-list-item');
        desktopEventItems.forEach(item => {
            const eventInfo = item.querySelector('.event-info');
            const descEl = item.querySelector('.event-description');
            if (eventInfo && descEl) {
                // Temporarily remove height constraint to measure natural content height
                const originalMaxHeight = item.style.maxHeight;
                item.style.maxHeight = 'none';

                // Measure the natural height of the content
                const naturalHeight = item.scrollHeight;

                // Restore the height constraint
                item.style.maxHeight = originalMaxHeight;

                // Get the constrained height (12rem = 192px typically)
                const constrainedHeight = item.clientHeight;

                // Check if content would naturally be taller than the constraint
                const hasOverflow = naturalHeight > constrainedHeight + 10; // 10px tolerance

                // Debug logging (remove after testing)
                if (descEl.textContent.includes('Illuminate Injustice') || descEl.textContent.includes('Trump and Epstein')) {
                    console.log('Debug overflow check:', {
                        title: item.querySelector('.event-title')?.textContent?.substring(0, 30),
                        naturalHeight,
                        constrainedHeight,
                        hasOverflow
                    });
                }

                if (hasOverflow) {
                    item.classList.add('has-overflow');
                } else {
                    item.classList.remove('has-overflow');
                    item.classList.remove('is-expanded');
                }
            }
        });

        // Check mobile events
        const mobileEventItems = document.querySelectorAll('#mobile-events-list .event-card');
        mobileEventItems.forEach(item => {
            const wrapper = item.querySelector('.event-content-wrapper-mobile');
            const descEl = item.querySelector('.event-description');
            if (wrapper && descEl) {
                const rawOverflow = wrapper.scrollHeight - wrapper.clientHeight;
                let hasOverflow = false;
                if (rawOverflow > 0) {
                    // Determine line height in pixels
                    let lineHeight = parseFloat(window.getComputedStyle(descEl).lineHeight);
                    if (isNaN(lineHeight)) {
                        // Fallback: estimate from font-size * 1.2
                        const fontSize = parseFloat(window.getComputedStyle(descEl).fontSize) || 16;
                        lineHeight = fontSize * 1.2;
                    }
                    // Require at least one full extra line hidden (i.e., 2+ lines total)
                    hasOverflow = rawOverflow >= lineHeight - 1; // small tolerance
                }

                if (hasOverflow) {
                    item.classList.add('has-overflow');
                } else {
                    item.classList.remove('has-overflow');
                    item.classList.remove('is-expanded');
                }
            }
        });
    }

    // Initial check for overflowing descriptions
    checkDescriptionOverflow();

    /**
     * Adds click listeners to expandable event items to toggle their expanded
     * state. This should be run after overflow is checked.
     */
    function initializeExpandableEvents() {
        // Initialize desktop events
        const desktopEventItems = document.querySelectorAll('.event-list-item.has-overflow');
        desktopEventItems.forEach(item => {
            // Use a named function for the listener to avoid adding multiple listeners
            // to the same element if this function is ever called more than once.
            if (!item.hasExpandListener) {
                item.addEventListener('click', toggleExpandDesktop);
                item.hasExpandListener = true;
            }
        });

        // Initialize mobile events
        const mobileEventItems = document.querySelectorAll('.event-card.has-overflow');
        mobileEventItems.forEach(item => {
            if (!item.hasExpandListener) {
                item.addEventListener('click', toggleExpandMobile);
                item.hasExpandListener = true;
            }
        });
    }

    function toggleExpandDesktop(event) {
        // Ignore clicks on links or inside the right-side image container
        if (
            event.target.tagName.toLowerCase() === 'a' ||
            event.target.closest('.event-image-right')
        ) {
            return; // do nothing
        }
        event.currentTarget.classList.toggle('is-expanded');
    }

    function toggleExpandMobile(event) {
        // Ignore clicks on links, buttons, or inside interactive elements
        if (
            event.target.tagName.toLowerCase() === 'a' ||
            event.target.tagName.toLowerCase() === 'button' ||
            event.target.closest('a') ||
            event.target.closest('button') ||
            event.target.closest('.map-links-mobile')
        ) {
            return; // do nothing
        }
        event.currentTarget.classList.toggle('is-expanded');
    }

    // Initialize expandable events on load
    initializeExpandableEvents();

    // Add a delayed initialization as backup for production environments
    setTimeout(() => {
        reCheckAndInitialize();
    }, 100);

    // Another backup initialization after a longer delay
    setTimeout(() => {
        reCheckAndInitialize();
    }, 500);

    // Re-check and re-initialize after filtering or resizing,
    // as visibility and overflow can change.
    function reCheckAndInitialize() {
        checkDescriptionOverflow();
        initializeExpandableEvents();
    }
});