document.addEventListener('DOMContentLoaded', () => {

    /* --- THEME TOGGLE --- */
    const themeToggleBtn = document.getElementById('theme-toggle');
    const icon = themeToggleBtn?.querySelector('i');
    if (themeToggleBtn) {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        if (currentTheme === 'dark' && icon) icon.className = 'ri-sun-line';

        themeToggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            if (icon) icon.className = newTheme === 'dark' ? 'ri-sun-line' : 'ri-moon-line';
        });
    }

    /* --- ANIMATE CHARTS / PROGRESS BARS ON LOAD --- */
    setTimeout(() => {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const targetWidth = bar.getAttribute('data-target-width');
            if (targetWidth) {
                bar.style.width = targetWidth;
            }
        });
    }, 100);

    /* --- ATS CIRCULAR SCORE COUNT UP --- */
    const scoreElements = document.querySelectorAll('.circular-score');
    scoreElements.forEach(el => {
        const textContent = el.textContent.trim();
        const targetNumber = parseInt(textContent, 10);

        if (!isNaN(targetNumber)) {
            let current = 0;
            const duration = 1200; // 1.2s smooth ease-out
            const start = performance.now();

            const animateScore = (time) => {
                const elapsed = time - start;
                const progress = Math.min(elapsed / duration, 1);

                // Ease out cubic
                const easeOut = 1 - Math.pow(1 - progress, 3);
                current = Math.floor(easeOut * targetNumber);
                el.textContent = current;

                if (progress < 1) {
                    requestAnimationFrame(animateScore);
                } else {
                    el.textContent = targetNumber;
                }
            };
            requestAnimationFrame(animateScore);
        }
    });

    /* --- FILE UPLOAD --- */
    const resumeInput = document.getElementById('resumeInput');
    const uploadBox = document.getElementById('uploadBox');
    const progressBar = document.getElementById('upload-progress-bar');
    const progressContainer = document.getElementById('upload-progress');

    if (uploadBox && resumeInput) {
        uploadBox.addEventListener('click', () => resumeInput.click());
        uploadBox.addEventListener('dragover', (e) => { e.preventDefault(); uploadBox.style.borderColor = '#6366f1'; });
        uploadBox.addEventListener('dragleave', (e) => { e.preventDefault(); uploadBox.style.borderColor = 'rgba(99, 102, 241, 0.4)'; });
        uploadBox.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadBox.style.borderColor = 'rgba(99, 102, 241, 0.4)';
            if (e.dataTransfer.files.length) {
                resumeInput.files = e.dataTransfer.files;
                handleFileUpload(e.dataTransfer.files[0]);
            }
        });
        resumeInput.addEventListener('change', function () {
            if (this.files.length > 0) handleFileUpload(this.files[0]);
        });
    }

    function handleFileUpload(file) {
        if (!file.name.endsWith('.pdf')) { alert('Please upload a PDF file.'); return; }
        uploadBox.classList.add('hidden');
        progressContainer.classList.remove('hidden');

        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            progressBar.style.width = `${progress}%`;
            if (progress >= 90) clearInterval(interval);
        }, 100);

        const formData = new FormData();
        formData.append("resume", file);
        const roleEl = document.getElementById('role-select');
        if (roleEl) formData.append('role', roleEl.value);

        fetch("/upload", { method: "POST", body: formData })
            .then(res => res.json())
            .then((data) => {
                clearInterval(interval);
                progressBar.style.width = '100%';
                setTimeout(() => {
                    if (data.success) {
                        window.location.href = "/dashboard";
                    } else {
                        alert(data.error || 'Upload error');
                        resetUpload();
                    }
                }, 500);
            }).catch(err => {
                console.error(err); alert("Upload failed."); resetUpload();
            });
    }

    function resetUpload() {
        uploadBox.classList.remove('hidden');
        progressContainer.classList.add('hidden');
        progressBar.style.width = '0%';
        if (resumeInput) resumeInput.value = '';
    }

    /* --- ROADMAP CHECKBOXES --- */
    const taskItems = document.querySelectorAll('.task-item');
    if (taskItems.length > 0) {
        const rpBar = document.getElementById('roadmap-progress');
        const rpPct = document.getElementById('roadmap-pct');
        const updateProgressUI = () => {
            const total = taskItems.length;
            const checked = document.querySelectorAll('.task-item.checked').length;
            const pct = total === 0 ? 100 : Math.round((checked / total) * 100);
            rpBar.style.width = `${pct}%`;
            if (rpPct) {
                animateTextCount(rpPct, pct);
            }
        };
        updateProgressUI();

        taskItems.forEach(item => {
            item.addEventListener('click', () => {
                item.classList.toggle('checked');
                updateProgressUI();
                const checkedTasks = Array.from(document.querySelectorAll('.task-item.checked')).map(el => el.getAttribute('data-task'));
                fetch('/api/update_progress', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ completed_tasks: checkedTasks })
                });
            });
        });
    }

    function animateTextCount(element, target) {
        const current = parseInt(element.textContent) || 0;
        if (current === target) return;
        const diff = target - current;
        let p = 0;
        const dur = setInterval(() => {
            p += diff > 0 ? 1 : -1;
            element.textContent = `${current + p}%`;
            if (p === diff) clearInterval(dur);
        }, 15);
    }

    /* --- GENERATE SUMMARY LOADER --- */
    const btnGen = document.getElementById('btn-generate-summary');
    const panelGen = document.getElementById('generated-summary');
    const txtGen = document.getElementById('summary-text');
    if (btnGen) {
        btnGen.addEventListener('click', () => {
            btnGen.innerHTML = 'Generating <i class="ri-loader-4-line ri-spin"></i>';
            setTimeout(() => {
                panelGen.style.display = 'block';
                panelGen.classList.add('fade-in-up');
                txtGen.innerHTML = `<strong>AI Suggested Insights:</strong><br><br>Highly motivated and results-oriented professional with a strong foundation in modern tech stack and problem solving...`;
                btnGen.innerHTML = 'Regenerate <i class="ri-magic-line"></i>';
            }, 1200);
        });
    }
    /* --- AI CHATBOT LOGIC --- */
    window.toggleChat = function () {
        const panel = document.getElementById('chat-panel');
        if (panel) panel.classList.toggle('active');
    };

    window.sendChat = function () {
        const input = document.getElementById('chat-input');
        const msgs = document.getElementById('chat-messages');
        const val = input.value.trim();
        if (!val) return;

        msgs.insertAdjacentHTML('beforeend', `<p class="user-msg">${val}</p>`);
        input.value = '';
        msgs.scrollTop = msgs.scrollHeight;

        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: val })
        })
            .then(r => r.json())
            .then(d => {
                msgs.insertAdjacentHTML('beforeend', `<p class="ai-msg">${d.reply}</p>`);
                msgs.scrollTop = msgs.scrollHeight;
            });
    };

    /* --- PARALLAX & CURSOR GLOW --- */
    const cursorGlow = document.getElementById('cursor-glow');
    const parallaxBg = document.getElementById('bg-parallax');
    let mX = window.innerWidth / 2, mY = window.innerHeight / 2;
    let cX = mX, cY = mY;

    document.addEventListener('mousemove', (e) => {
        mX = e.clientX; mY = e.clientY;

        if (parallaxBg) {
            const xOffset = ((mX / window.innerWidth) - 0.5) * -20;
            const yOffset = ((mY / window.innerHeight) - 0.5) * -20;
            parallaxBg.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
        }
    });

    const animateCursor = () => {
        const diffX = mX - cX;
        const diffY = mY - cY;
        cX += diffX * 0.15;
        cY += diffY * 0.15;

        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        if (cursorGlow) {
            cursorGlow.style.left = `${cX}px`;
            cursorGlow.style.top = `${cY}px`;
            cursorGlow.style.background = isDark ? `radial-gradient(circle, rgba(168,85,247,0.8) 0%, transparent 70%)`
                : `radial-gradient(circle, rgba(99,102,241,0.6) 0%, transparent 70%)`;
        }
        requestAnimationFrame(animateCursor);
    };
    animateCursor();

    /* --- MAGNETIC PHYSICS --- */
    document.querySelectorAll('.btn, .btn-icon').forEach(btn => {
        btn.classList.add('magnetic');
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;
            btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px) scale(1.05)`;
            if (cursorGlow) {
                cursorGlow.style.width = '600px'; cursorGlow.style.height = '600px'; cursorGlow.style.opacity = '0.3';
            }
        });
        btn.addEventListener('mouseleave', () => {
            btn.style.transform = `translate(0px, 0px) scale(1)`;
            if (cursorGlow) {
                cursorGlow.style.width = '400px'; cursorGlow.style.height = '400px'; cursorGlow.style.opacity = '0.15';
            }
        });
    });
});
