
function addDestination() {
    const container = document.getElementById('destinationsContainer');
    const newInput = document.createElement('div');
    newInput.className = 'destination-input';

    newInput.innerHTML = `
        <input type="text" name="destinations"
               class="destination-field"
               placeholder="Enter destination" required>
        <button type="button" class="remove-destination"
                onclick="removeDestination(this)">Remove</button>
    `;

    container.appendChild(newInput);
}

function removeDestination(button) {
    const inputDiv = button.parentElement;

    if (document.querySelectorAll('.destination-input').length > 1) {
        inputDiv.remove();
    } else {
        alert('At least one destination is required.');
    }
}

async function generateItinerary(from, destinations, budget, startDate, duration, travelType) {
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

    if (!response.ok || !data.success) {
        throw new Error(data.message || 'Failed to generate itinerary.');
    }

    return data.itinerary;
}

document.addEventListener('DOMContentLoaded', function () {

    const tripForm = document.getElementById('tripForm');
    const itineraryResult = document.getElementById('itineraryResult');
    const outputDiv = document.getElementById('output');
    const loader = document.getElementById('loader');
    const addDestinationBtn = document.getElementById('addDestinationBtn');

    const saveForm = document.getElementById('saveItineraryForm');
    const downloadBtn = document.getElementById('downloadBtn');

    if (!tripForm || !itineraryResult || !outputDiv || !loader) {
        console.error('Required page elements not found.');
        return;
    }

    if (addDestinationBtn) {
        addDestinationBtn.addEventListener('click', addDestination);
    }

    // GENERATE ITINERARY
    tripForm.addEventListener('submit', async function (event) {

        event.preventDefault();

        const destinationFields = document.querySelectorAll('.destination-field');

        const destinations = Array.from(destinationFields)
            .map(field => field.value.trim())
            .filter(value => value !== '');

        const normalizedDestinations = destinations.map(value =>
            value.toLowerCase().replace(/\s+/g, ' ')
        );

        const from = tripForm.elements['from_location'].value.trim();
        const budget = tripForm.elements['budget'].value;
        const startDate = tripForm.elements['startDate'].value;
        const duration = parseInt(tripForm.elements['duration'].value);
        const travelType = tripForm.elements['travelType'].value;

        if (!from || destinations.length === 0 ||
            !budget || !startDate || !duration || !travelType) {
            alert('Please fill in all fields.');
            return;
        }

        if (new Set(normalizedDestinations).size !== normalizedDestinations.length) {
            alert('Please remove duplicate destinations.');
            return;
        }

        if (new Date(startDate + 'T00:00:00') < new Date(new Date().toDateString())) {
            alert('Start date cannot be in the past.');
            return;
        }

        loader.style.display = 'block';
        itineraryResult.style.display = 'none';

        if (saveForm) saveForm.style.display = 'none';
        if (downloadBtn) downloadBtn.style.display = 'none';

        try {

            const itineraryHTML = await generateItinerary(
                from,
                destinations,
                budget,
                startDate,
                duration,
                travelType
            );

            outputDiv.innerHTML = itineraryHTML;

            itineraryResult.style.display = 'block';
            itineraryResult.classList.add('show');

            // POPULATE SAVE FORM
            if (saveForm) {

                document.getElementById('itinerary_content').value = itineraryHTML;

                document.getElementById('savedDestination').value =
                    destinations.join(', ');

                document.getElementById('savedStartDate').value = startDate;

                document.getElementById('savedDuration').value = duration;

                document.getElementById('from_location_hidden').value = from;

                document.getElementById('hiddenBudget').value = budget;

                saveForm.style.display = 'block';
            }

            if (downloadBtn) {
                downloadBtn.style.display = 'inline-block';
            }

        } catch (error) {

            console.error('Generation error:', error);

            outputDiv.textContent = error.message || 'Failed to generate itinerary.';

            itineraryResult.style.display = 'block';
            itineraryResult.classList.add('show');

        } finally {

            loader.style.display = 'none';

        }
    });


    // SAVE ITINERARY
    if (saveForm) {

        saveForm.addEventListener('submit', async function (event) {

            event.preventDefault();

            const saveButton = saveForm.querySelector('button[type="submit"]');

            saveButton.disabled = true;
            saveButton.textContent = 'Saving...';

            try {

                const response = await fetch(saveForm.action, {
                    method: 'POST',
                    body: new FormData(saveForm)
                });

                const data = await response.json();

                if (!response.ok || !data.success) {
                    throw new Error(data.message || 'Unable to save itinerary.');
                }

                alert('Your itinerary has been saved successfully!');

                window.location.href = data.redirect_url;

            } catch (error) {

                console.error('Save error:', error);

                alert('Error saving itinerary: ' + error.message);

                saveButton.disabled = false;
                saveButton.textContent = 'Save';

            }

        });

    }

});
