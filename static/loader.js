// Global Page Loader System
(function() {
    'use strict';

    // Create loader HTML
    function createLoader() {
        // Check if loader already exists
        if (document.getElementById('page-loader')) {
            return;
        }

        const loaderHTML = `
            <div id="page-loader">
                <div class="loader-content">
                    <img src="/static/logo.svg" alt="Medipure" class="loader-logo">
                    <div class="loader-spinner"></div>
                    <div class="loader-text">Loading...</div>
                    <div class="loader-subtext">Please wait</div>
                </div>
            </div>
            <div class="nav-loader"></div>
        `;
        
        document.body.insertAdjacentHTML('afterbegin', loaderHTML);
    }

    // Show loader
    function showLoader() {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.classList.remove('hidden');
        }
    }

    // Hide loader
    function hideLoader() {
        const loader = document.getElementById('page-loader');
        if (loader) {
            loader.classList.add('hidden');
        }
    }

    // Show navigation loader (top bar)
    function showNavLoader() {
        const navLoader = document.querySelector('.nav-loader');
        if (navLoader) {
            navLoader.classList.add('active');
        }
    }

    // Hide navigation loader
    function hideNavLoader() {
        const navLoader = document.querySelector('.nav-loader');
        if (navLoader) {
            navLoader.classList.remove('active');
        }
    }

    // Initialize on page load
    function init() {
        createLoader();
        
        // Hide loader when page is fully loaded
        if (document.readyState === 'complete') {
            hideLoader();
        } else {
            window.addEventListener('load', function() {
                setTimeout(hideLoader, 300); // Small delay for smooth transition
            });
        }

        // Intercept all navigation links
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a');
            
            // Check if it's a navigation link (not external, not anchor, not download)
            if (link && 
                link.href && 
                !link.href.startsWith('javascript:') &&
                !link.href.includes('#') &&
                !link.hasAttribute('download') &&
                !link.target === '_blank' &&
                link.href.startsWith(window.location.origin)) {
                
                // Don't show loader for same page
                if (link.href === window.location.href) {
                    return;
                }

                // Show loader
                showNavLoader();
                setTimeout(showLoader, 200); // Show full loader after 200ms if page hasn't loaded
            }
        });

        // Show loader on form submissions
        document.addEventListener('submit', function(e) {
            const form = e.target;
            
            // Don't show loader if form has data-no-loader attribute
            if (!form.hasAttribute('data-no-loader')) {
                showNavLoader();
                setTimeout(showLoader, 200);
            }
        });

        // Show loader on browser back/forward
        window.addEventListener('pageshow', function(event) {
            if (event.persisted) {
                hideLoader();
                hideNavLoader();
            }
        });

        // Hide loader if page is hidden (user switched tabs)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                hideNavLoader();
            }
        });

        // Fallback: hide loader after 10 seconds (in case something goes wrong)
        setTimeout(function() {
            hideLoader();
            hideNavLoader();
        }, 10000);
    }

    // Run init when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose functions globally for manual control
    window.MedipureLoader = {
        show: showLoader,
        hide: hideLoader,
        showNav: showNavLoader,
        hideNav: hideNavLoader
    };
})();
