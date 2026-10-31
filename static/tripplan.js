document.addEventListener('DOMContentLoaded', function() {
    const tripForm = document.getElementById('tripForm');
    const itineraryResult = document.getElementById('itineraryResult');
    const outputDiv = document.getElementById('output');
    const loader = document.getElementById('loader'); // may be null
    const saveItineraryForm = document.getElementById('saveItineraryForm');

    if (!tripForm) {
        console.error('Trip Form not found');
        return;
    }
    if (!itineraryResult) {
        console.error('Itinerary Result not found');
        return;
    }
    if (!outputDiv) {
        console.error('Output Div not found');
        return;
    }

    console.log('Trip Form:', tripForm);
    console.log('Itinerary Result:', itineraryResult);
    console.log('Output Div:', outputDiv);
    console.log('Save Itinerary Form:', saveItineraryForm);

    // Helper: safe show/hide loader
    function showLoader() { if (loader) loader.style.display = 'block'; }
    function hideLoader() { if (loader) loader.style.display = 'none'; }

    // Placeholder: ensure you have these functions defined elsewhere
    // async function generateItinerary(from, destinations, budget, startDate, duration, travelType) { ... }
    // function calculateEndDate(startDate, duration) { ... }

    if (saveItineraryForm) {
        saveItineraryForm.addEventListener('submit', async function(event) {
            event.preventDefault();
            const actionUrl = saveItineraryForm.action || '/save_itinerary';
            const formData = new FormData(saveItineraryForm);

            try {
                const response = await fetch(actionUrl, {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin'
                });

                const data = await response.json();
                if (data.success) {
                    alert('Itinerary saved successfully!');
                    // Use absolute redirect only if provided
                    if (data.redirect_url) window.location.href = data.redirect_url;
                } else {
                    alert('Failed to save itinerary. Please try again.');
                    console.error('Save itinerary response:', data);
                }
            } catch (error) {
                alert('An error occurred while saving the itinerary.');
                console.error('Error saving itinerary:', error);
            }
        });
    }

    tripForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        // Collect multiple destinations (only non-empty)
        const destinationFields = document.querySelectorAll('.destination-field');
        const destinations = [];
        destinationFields.forEach(field => {
            if (field && field.value && field.value.trim() !== '') {
                destinations.push(field.value.trim());
            }
        });

        const from = (tripForm.from_location && tripForm.from_location.value) ? tripForm.from_location.value.trim() : '';
        const budget = tripForm.budget ? tripForm.budget.value : '';
        const startDate = tripForm.startDate ? tripForm.startDate.value : '';
        const durationRaw = tripForm.duration ? tripForm.duration.value : '';
        const duration = parseInt(durationRaw, 10);
        const travelType = tripForm.travelType ? tripForm.travelType.value : '';

        // Basic required fields check
        if (!from || destinations.length === 0 || !budget || !startDate || !duration || !travelType) {
            alert('Please fill in all fields.');
            return;
        }

        // Validate startDate properly
        const start = new Date(startDate);
        if (isNaN(start.getTime())) {
            alert('Invalid start date.');
            return;
        }
        const currentYear = new Date().getFullYear();
        const startYear = start.getFullYear();
        if (startYear < currentYear) {
            alert('Start date year cannot be in the past.');
            return;
        }

        // --- Country-specific validation (choose one) ---
        // Option A: Prevent both "from" and any destination containing literal 'india' (your original logic)
        // if (from.toLowerCase().includes('india') && destinations.some(d => d.toLowerCase().includes('india'))) {
        //     alert('From and Destinations cannot both be in India. Please choose different destinations.');
        //     return;
        // }

        // Option B (recommended): Prevent identical from and destination values (strict equality)
        // (use this if you want to stop user accidentally selecting the same city twice)
        if (destinations.some(d => d.toLowerCase() === from.toLowerCase())) {
            // if you *do* allow domestic trips, remove this block
            const ok = confirm('One of the destinations matches the origin. Proceed anyway?');
            if (!ok) return;
        }
        // --- end country validation ---

        // Show loader & hide result area
        showLoader();
        itineraryResult.style.display = 'none';
        itineraryResult.classList.remove('show');

        try {
            // Ensure generateItinerary exists
            if (typeof generateItinerary !== 'function') {
                throw new Error('generateItinerary() is not defined. Please implement it.');
            }

            const itineraryHTML = await generateItinerary(from, destinations, budget, startDate, duration, travelType);

            // Check result
            if (!itineraryHTML || typeof itineraryHTML !== 'string') {
                throw new Error('Invalid itinerary HTML from generateItinerary');
            }

            // Insert HTML (be sure the server returns safe HTML)
            outputDiv.innerHTML = itineraryHTML;
            itineraryResult.style.display = 'block';
            itineraryResult.classList.add('show');

            // Enable save form and set hidden inputs if present
            if (saveItineraryForm) {
                saveItineraryForm.style.display = 'block';

                const elItineraryContent = document.getElementById('itinerary_content');
                if (elItineraryContent) elItineraryContent.value = itineraryHTML;

                const elSavedHighlights = document.getElementById('savedHighlights');
                if (elSavedHighlights) {
                    elSavedHighlights.value = [
                        `From: ${from}`,
                        `Destinations: ${destinations.join(', ')}`,
                        `Start Date: ${startDate}`,
                        `Duration: ${duration} days`,
                        `Budget: ${budget}`,
                        `Travel Type: ${travelType}`
                    ].join(' | ');
                }

                const elEndDateHidden = document.getElementById('endDateHidden');
                if (elEndDateHidden && typeof calculateEndDate === 'function') {
                    elEndDateHidden.value = calculateEndDate(startDate, duration);
                } else if (elEndDateHidden) {
                    // fallback simple calc
                    const end = new Date(start);
                    end.setDate(end.getDate() + duration);
                    elEndDateHidden.value = end.toISOString().slice(0,10);
                }

                const elHiddenBudget = document.getElementById('hiddenBudget');
                if (elHiddenBudget) elHiddenBudget.value = budget;

                const elFromHidden = document.getElementById('from_location_hidden');
                if (elFromHidden) elFromHidden.value = from;

                const elTravelTypeHidden = document.getElementById('travel_type_hidden');
                if (elTravelTypeHidden) elTravelTypeHidden.value = travelType;

                // Set single destination and dates for your backend
                const destInput = saveItineraryForm.querySelector('input[name="destination"]');
                const startInput = saveItineraryForm.querySelector('input[name="start_date"]');
                const durInput = saveItineraryForm.querySelector('input[name="duration"]');
                if (destInput) destInput.value = destinations.join(', ');
                if (startInput) startInput.value = startDate;
                if (durInput) durInput.value = duration;

                // Debug logs (remove in production)
                console.log('Hidden inputs set for saveItineraryForm:',
                    { itineraryLength: itineraryHTML.length, destinations, startDate, duration }
                );
            }

            const downloadBtn = document.getElementById('downloadBtn');
            if (downloadBtn) {
                downloadBtn.style.display = 'inline-block';
            }

        } catch (error) {
            outputDiv.innerHTML = '<p>Failed to generate itinerary. Please try again later.</p>';
            console.error('Error generating itinerary:', error);
            itineraryResult.style.display = 'block';
            itineraryResult.classList.add('show');
        } finally {
            hideLoader();
        }
    });
});
