document.addEventListener('DOMContentLoaded', function() {
    const tripForm = document.getElementById('tripForm');
    const itineraryResult = document.getElementById('itineraryResult');
    const outputDiv = document.getElementById('output');
    const loader = document.getElementById('loader');

    console.log('Trip Form:', tripForm);
    console.log('Itinerary Result:', itineraryResult);
    console.log('Output Div:', outputDiv);
    console.log('Loader:', loader);

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
    if (!loader) {
        console.error('Loader not found');
        return;
    }

    // Add event listener for form submission
    tripForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        // Collect multiple destinations
        const destinationFields = document.querySelectorAll('.destination-field');
        const destinations = [];
        destinationFields.forEach(field => {
            if (field.value.trim() !== '') {
                destinations.push(field.value.trim());
            }
        });

        const from = tripForm.from_location.value.trim();
        const budget = tripForm.budget.value;
        const startDate = tripForm.startDate.value;
        const duration = parseInt(tripForm.duration.value);
        const travelType = tripForm.travelType.value;

        // Validation: Check if from and destinations are both in India (simple check)
        const fromLower = from.toLowerCase();
        const destinationsLower = destinations.map(d => d.toLowerCase());
        if (fromLower.includes('india') && destinationsLower.some(d => d.includes('india'))) {
            alert('From and Destinations cannot both be in India. Please choose different destinations.');
            return;
        }

        // Validation: Check startDate year is current year or later
        const currentYear = new Date().getFullYear();
        const startYear = new Date(startDate).getFullYear();
        if (startYear < currentYear) {
            alert('Start date year cannot be in the past.');
            return;
        }

        if (!from || destinations.length === 0 || !budget || !startDate || !duration || !travelType) {
            alert('Please fill in all fields.');
            return;
        }

        loader.style.display = 'block';
        itineraryResult.style.display = 'none';
        itineraryResult.classList.remove('show');

        try {
            const itineraryHTML = await generateItinerary(from, destinations, budget, startDate, duration, travelType);
            outputDiv.innerHTML = itineraryHTML;
            itineraryResult.style.display = 'block';
            itineraryResult.classList.add('show');

            // Show save itinerary form and download button
            const saveItineraryForm = document.getElementById('saveItineraryForm');
            if (saveItineraryForm) {
                saveItineraryForm.style.display = 'block';
                // Populate hidden inputs
                document.getElementById('itinerary_content').value = itineraryHTML;

                // Create simplified summary for savedHighlights
                const summary = `
                    From: ${from}
                    Destinations: ${destinations.join(', ')}
                    Start Date: ${startDate}
                    Duration: ${duration} days
                    Budget: ${budget}
                    Travel Type: ${travelType}
                `.trim();

                document.getElementById('savedHighlights').value = summary;
                document.getElementById('endDateHidden').value = calculateEndDate(startDate, duration);
                document.getElementById('hiddenBudget').value = budget;
                document.getElementById('from_location_hidden').value = from;
                document.getElementById('travel_type_hidden').value = travelType;

                // Set hidden inputs for destination, start_date, and duration dynamically
                saveItineraryForm.querySelector('input[name="destination"]').value = destinations.join(', ');
                saveItineraryForm.querySelector('input[name="start_date"]').value = startDate;
                saveItineraryForm.querySelector('input[name="duration"]').value = duration;

                // Debug logs for hidden inputs
                console.log('Save Itinerary Form Hidden Inputs:');
                console.log('itinerary_content:', document.getElementById('itinerary_content').value);
                console.log('savedHighlights:', document.getElementById('savedHighlights').value);
                console.log('endDateHidden:', document.getElementById('endDateHidden').value);
                console.log('hiddenBudget:', document.getElementById('hiddenBudget').value);
                console.log('from_location_hidden:', document.getElementById('from_location_hidden').value);
                console.log('travel_type_hidden:', document.getElementById('travel_type_hidden').value);
                console.log('destination:', saveItineraryForm.querySelector('input[name="destination"]').value);
                console.log('start_date:', saveItineraryForm.querySelector('input[name="start_date"]').value);
                console.log('duration:', saveItineraryForm.querySelector('input[name="duration"]').value);
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
            loader.style.display = 'none';
        }
    });
});
