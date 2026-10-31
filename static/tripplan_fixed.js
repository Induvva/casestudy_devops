// Utility functions for destination management
function addDestination() {
    const container = document.getElementById('destinationsContainer');
    const newInput = document.createElement('div');
    newInput.className = 'destination-input';
    newInput.innerHTML = `
        <input type="text" name="destinations" class="destination-field" placeholder="Enter destination" required>
        <button type="button" class="remove-destination" onclick="removeDestination(this)">Remove</button>
    `;
    container.appendChild(newInput);
}

function removeDestination(button) {
    const container = button.parentElement;
    container.remove();
}

function calculateEndDate(startDate, duration) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + duration);
    return date.toISOString().split('T')[0];
}

document.addEventListener('DOMContentLoaded', function() {
    const tripForm = document.getElementById('tripForm');
    const itineraryResult = document.getElementById('itineraryResult');
    const outputDiv = document.getElementById('output');
    const loader = document.getElementById('loader');
    const addDestinationBtn = document.getElementById('addDestinationBtn');

    console.log('Trip Form:', tripForm);
    console.log('Itinerary Result:', itineraryResult);
    console.log('Output Div:', outputDiv);
    console.log('Loader:', loader);

    // Check if elements are null
    if (!tripForm) {
        console.error('Trip Form not found');
    }
    if (!itineraryResult) {
        console.error('Itinerary Result not found');
    }
    if (!outputDiv) {
        console.error('Output Div not found');
    }
    if (!loader) {
        console.error('Loader not found');
    }

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
    if (addDestinationBtn) {
        addDestinationBtn.addEventListener('click', addDestination);
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
            const response = await fetch('/generate_itinerary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    from: from,
                    destination: destinations.join(', '),
                    budget: budget,
                    startDate: startDate,
                    duration: duration,
                    travelType: travelType
                })
            });

            const data = await response.json();
            if (data.success) {
                outputDiv.innerHTML = data.itinerary;
                itineraryResult.style.display = 'block';
                itineraryResult.classList.add('show');

                // Show save itinerary form and download button
                const saveItineraryForm = document.getElementById('saveItineraryForm');
                if (saveItineraryForm) {
                    saveItineraryForm.style.display = 'block';
                    // Populate hidden inputs
                    document.getElementById('itinerary_content').value = data.itinerary;

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
                }
                const downloadBtn = document.getElementById('downloadBtn');
                if (downloadBtn) {
                    downloadBtn.style.display = 'inline-block';
                }
            } else {
                outputDiv.innerHTML = '<p>Failed to generate itinerary. Please try again later.</p>';
                console.error('Error generating itinerary:', data.message);
                itineraryResult.style.display = 'block';
                itineraryResult.classList.add('show');
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

function calculateEndDate(startDate, duration) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + duration);
    return date.toISOString().split('T')[0];
}
