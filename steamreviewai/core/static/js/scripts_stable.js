const reviewsForm = document.getElementById('reviews-form');
const searchForm = document.getElementById('search-form');
const searchResultContainer = document.getElementById('search-result-container');
const toggleReviews = document.querySelectorAll('#toggle-reviews');
const toggleSearch = document.querySelectorAll('#toggle-search');
const toggleTheme = document.getElementById('toggle-theme');

// Функция для включения/выключения всех кнопок
function setButtonsState(disabled) {
    const buttons = document.querySelectorAll("button");
    buttons.forEach(button => {
        button.disabled = disabled;
    });
}

toggleReviews.forEach(button => {
    button.addEventListener('click', () => {
        reviewsForm.style.display = 'block';
        searchForm.style.display = 'none';
        searchResultContainer.style.display = 'none';
        toggleReviews.forEach(btn => btn.classList.add('btn-primary'));
        toggleReviews.forEach(btn => btn.classList.remove('btn-outline-primary'));
        toggleSearch.forEach(btn => btn.classList.add('btn-outline-primary'));
        toggleSearch.forEach(btn => btn.classList.remove('btn-primary'));
    });
});

toggleSearch.forEach(button => {
    button.addEventListener('click', () => {
        reviewsForm.style.display = 'none';
        searchForm.style.display = 'block';
        searchResultContainer.style.display = 'none';
        toggleSearch.forEach(btn => btn.classList.add('btn-primary'));
        toggleSearch.forEach(btn => btn.classList.remove('btn-outline-primary'));
        toggleReviews.forEach(btn => btn.classList.add('btn-outline-primary'));
        toggleReviews.forEach(btn => btn.classList.remove('btn-primary'));
    });
});

toggleTheme.addEventListener('click', () => {
    document.body.classList.toggle('dark-mode');
    const icon = toggleTheme.querySelector('i');
    if (document.body.classList.contains('dark-mode')) {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    } else {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
});

document.getElementById("submitReview").addEventListener("click", async function () {
    const formData = new FormData(document.getElementById("reviewForm"));
    const resultDiv = document.getElementById("result");
    const idleLoader = document.getElementById('inner-load-spinner');

    setButtonsState(true);
    resultDiv.innerHTML = "";

    idleLoader.style.display = "block";

    try {
        await new Promise(resolve => setTimeout(resolve, 500));

        const response = await fetch("/process", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Неизвестная ошибка");
        }

        resultDiv.innerHTML = `<p>${data.review}</p>`;
    } catch (error) {
        resultDiv.innerHTML = `<p class="text-danger">${error.message}</p>`;
    } finally {
        setButtonsState(false);
        idleLoader.style.display = "none";
    }
});

document.getElementById("submitSearch").addEventListener("click", async function () {
    const tags = document.getElementById("tags").value;
    const resultDiv = document.getElementById("search-result");
    const idleLoaderFilter = document.getElementById("inner-load-spinner-filter");

    setButtonsState(true);
    resultDiv.innerHTML = "<p>Идёт поиск...</p>";

    idleLoaderFilter.style.display = "block";

    try {
        await new Promise(resolve => setTimeout(resolve, 500));

        const response = await fetch("/search_games", {
            method: "POST",
            headers: {
                "Content-Type": "text/plain"
            },
            body: tags
        });

        if (response.ok) {
            const text = await response.text();
            searchResultContainer.style.display = 'block';
            resultDiv.innerHTML = `<pre>${text}</pre>`;
        } else {
            const errorText = await response.text();
            searchResultContainer.style.display = 'block';
            resultDiv.innerHTML = `<p class="text-danger">Ошибка: ${errorText}</p>`;
        }
    } catch (error) {
        searchResultContainer.style.display = 'block';
        resultDiv.innerHTML = `<p class="text-danger">Ошибка: ${error.message}</p>`;
    } finally {
        setButtonsState(false);
        idleLoaderFilter.style.display = "none";
    }
});

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".modal-body img").forEach(img => {
        img.addEventListener("click", function () {
            const modalImage = document.getElementById("modalImage");
            modalImage.src = this.src;
            modalImage.classList.add("w-100");
            new bootstrap.Modal(document.getElementById("imageModal")).show();
        });
    });
});


