const generateBtn = document.getElementById('generateBtn');
const refineBtn = document.getElementById('refineBtn');
const newLogoBtn = document.getElementById('newLogoBtn');
const downloadBtn = document.getElementById('downloadBtn');
const companyName = document.getElementById('companyName');
const styleSelect = document.getElementById('styleSelect');
const logoForm = document.getElementById('logoForm');
const customPrompt = document.getElementById('customPrompt');
const refinementPrompt = document.getElementById('refinementPrompt');
const generatorSection = document.getElementById('generatorSection');
const resultSection = document.getElementById('resultSection');
const resultImage = document.getElementById('resultImage');
const usedPrompt = document.getElementById('usedPrompt');
const seedInfo = document.getElementById('seedInfo');
const modePill = document.getElementById('modePill');
const errorMessage = document.getElementById('errorMessage');

let currentPrompt = '';
let currentSeed = null;
let currentCompanyName = '';
let currentStyle = '';
let currentLogoForm = '';

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 6000);
}

function setLoading(button, isLoading) {
    const btnText = button.querySelector('.btn-text');
    const loader = button.querySelector('.loader');
    if (isLoading) {
        btnText.style.display = 'none';
        loader.style.display = 'block';
        button.disabled = true;
    } else {
        btnText.style.display = 'inline';
        loader.style.display = 'none';
        button.disabled = false;
    }
}

function renderResult(data) {
    currentPrompt = data.prompt;
    currentSeed = data.seed;
    currentCompanyName = companyName.value.trim() || currentCompanyName;
    currentStyle = styleSelect.value;
    currentLogoForm = logoForm.value;

    resultImage.src = data.image_url || `data:image/png;base64,${data.image}`;
    downloadBtn.href = data.download_url || resultImage.src;
    downloadBtn.download = `${currentCompanyName || 'generated'}-logo.png`;
    usedPrompt.textContent = data.prompt;
    seedInfo.textContent = `Seed: ${data.seed}`;
    modePill.textContent = data.mode === 'demo' ? 'demo mode' : 'Yandex Art';

    generatorSection.style.display = 'none';
    resultSection.style.display = 'block';
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

generateBtn.addEventListener('click', async () => {
    const name = companyName.value.trim();
    if (!name) {
        showError('Введите название компании');
        return;
    }

    setLoading(generateBtn, true);
    errorMessage.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                company_name: name,
                style: styleSelect.value,
                logo_form: logoForm.value,
                custom_prompt: customPrompt.value
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка генерации');
        }
        renderResult(data);
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(generateBtn, false);
    }
});

refineBtn.addEventListener('click', async () => {
    const refinement = refinementPrompt.value.trim();
    if (!refinement) {
        showError('Опишите, что нужно изменить в логотипе');
        return;
    }

    setLoading(refineBtn, true);
    errorMessage.style.display = 'none';

    try {
        const response = await fetch('/refine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                original_prompt: currentPrompt,
                refinement: refinement,
                seed: currentSeed,
                company_name: currentCompanyName,
                style: currentStyle,
                logo_form: currentLogoForm
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка доработки');
        }
        renderResult(data);
        refinementPrompt.value = '';
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(refineBtn, false);
    }
});

newLogoBtn.addEventListener('click', () => {
    resultSection.style.display = 'none';
    generatorSection.style.display = 'block';
    refinementPrompt.value = '';
    currentPrompt = '';
    currentSeed = null;
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

companyName.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        generateBtn.click();
    }
});

customPrompt.addEventListener('keypress', (event) => {
    if (event.key === 'Enter' && event.ctrlKey) {
        generateBtn.click();
    }
});

refinementPrompt.addEventListener('keypress', (event) => {
    if (event.key === 'Enter' && event.ctrlKey) {
        refineBtn.click();
    }
});
