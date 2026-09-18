// SKINOZ Mini App Client Logic
const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
    try {
        tg.ready();
        tg.expand();
    } catch(e) {}
}

let currentUser = {
    tg_id: 123456789,
    first_name: "O'yinchi",
    balance: 0.00,
    trade_url: "",
    inventory: []
};

let allCases = [];
let allSkins = [];
let userInventory = [];
let currentCase = null;
let lastWonSkin = null;

let currentCurrency = 'UZS';
let isSoundOn = true;

function triggerHaptic(type = 'light') {
    if (tg && tg.HapticFeedback) {
        try {
            if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
            else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
            else tg.HapticFeedback.impactOccurred(type);
        } catch(e) {}
    }
}

function formatMoney(amountUsd) {
    if (currentCurrency === 'USD') {
        return `$ ${amountUsd.toFixed(2)}`;
    }
    return `💎 ${Math.round(amountUsd * 12500).toLocaleString('uz-UZ')}`;
}

function updateUI() {
    const balEl = document.getElementById("userBalance");
    if (balEl) {
        if (currentCurrency === 'USD') {
            balEl.innerText = `$ ${currentUser.balance.toFixed(2)}`;
        } else {
            balEl.innerText = Math.round(currentUser.balance * 12500).toLocaleString('uz-UZ');
        }
    }
    if (typeof updateDoubleBalLabel === "function") updateDoubleBalLabel();
    if (typeof updateX50BalLabel === "function") updateX50BalLabel();
}

function renderCases() {
    const grid = document.getElementById("casesGrid");
    if (!grid) return;
    grid.innerHTML = "";
    if (!allCases.length) {
        allCases = [
            { id: "free", name: "🎁 FREE DAILY", badge: "KUNLIK", price: 0, image: "images/case_free.png" },
            { id: "revolution", name: "⚡ REVOLUTION CASE", badge: "HOT", price: 1.99, image: "images/case_revolution.png" },
            { id: "kilowatt", name: "⚡ KILOWATT CASE", badge: "NEW", price: 3.50, image: "images/case_kilowatt.png" },
            { id: "dreams", name: "🔥 DREAMS & NIGHTMARES", badge: "RARE", price: 5.99, image: "images/case_dreams.png" },
            { id: "clutch", name: "🧤 CLUTCH GLOVES", badge: "GLOVES", price: 18.00, image: "images/case_clutch.png" },
            { id: "knife_fever", name: "🔪 KNIFE & GLOVES", badge: "VIP", price: 35.00, image: "images/case_knives.png" },
            { id: "dragon_vault", name: "👑 DRAGON VAULT", badge: "VIP", price: 99.00, image: "images/case_dragon.png" }
        ];
    }
    allCases.forEach(c => {
        const div = document.createElement("div");
        div.className = "case-card";
        const priceLabel = c.price > 0 ? formatMoney(c.price) : "BEPUL";
        div.innerHTML = `
            <span class="case-tag-badge">${c.badge || 'HOT'}</span>
            <img src="${c.image}" alt="${c.name}">
            <h4>${c.name}</h4>
            <div class="case-card-price">${priceLabel}</div>
        `;
        div.onclick = () => openCaseModal(c);
        grid.appendChild(div);
    });
}

function getCaseSkins(c) {
    if (!c || !c.items || !allSkins.length) return allSkins;
    const skins = [];
    c.items.forEach(it => {
        const s = allSkins.find(skin => skin.id === it.skin_id);
        if (s) skins.push(s);
    });
    return skins.length > 0 ? skins : allSkins;
}

function openCaseModal(c) {
    triggerHaptic('light');
    currentCase = c;
    const nameEl = document.getElementById("modalCaseName");
    const priceEl = document.getElementById("modalCasePrice");
    if (nameEl) nameEl.innerText = c.name;
    if (priceEl) priceEl.innerText = c.price > 0 ? formatMoney(c.price) : "BEPUL";
    renderCaseItems(c);
    resetStrip(c);
    const modal = document.getElementById("caseModal");
    if (modal) modal.classList.add("active");
}

function renderCaseItems(c) {
    const container = document.getElementById("caseItemsList");
    if (!container) return;
    const skins = getCaseSkins(c);
    container.innerHTML = `<h4 style="color:#aaa; font-size:12px; margin: 15px 0 8px; text-transform:uppercase; letter-spacing:1px;">Keys tarkibi:</h4>`;
    
    const itemsWrap = document.createElement("div");
    itemsWrap.style.display = "flex";
    itemsWrap.style.flexWrap = "wrap";
    itemsWrap.style.gap = "8px";
    itemsWrap.style.justifyContent = "center";

    skins.forEach(s => {
        const card = document.createElement("div");
        card.style.background = "#14181c";
        card.style.border = `1px solid ${s.color || '#333'}`;
        card.style.borderRadius = "8px";
        card.style.padding = "6px";
        card.style.width = "75px";
        card.style.textAlign = "center";
        card.innerHTML = `
            <img src="${s.image}" style="width: 100%; height: 45px; object-fit: contain;">
            <div style="font-size: 10px; font-weight: 600; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${s.name.replace('★ ', '')}</div>
            <div style="font-size: 9px; color: ${s.color}; font-weight: bold;">${formatMoney(s.price)}</div>
        `;
        itemsWrap.appendChild(card);
    });
    container.appendChild(itemsWrap);
}

function resetStrip(c) {
    const strip = document.getElementById("rouletteStrip");
    if (!strip) return;
    strip.style.transition = "none";
    strip.style.transform = "translateX(0px)";
    strip.innerHTML = "";

    const caseSkins = getCaseSkins(c);
    const count = caseSkins.length > 0 ? 20 : 10;
    for (let i = 0; i < count; i++) {
        const randSkin = caseSkins.length > 0 ? caseSkins[Math.floor(Math.random() * caseSkins.length)] : { image: "images/skin_nomad.png", color: "#10e87b" };
        strip.innerHTML += `
            <div class="strip-item" style="border-bottom: 2px solid ${randSkin.color || '#10e87b'};">
                <img src="${randSkin.image}">
            </div>
        `;
    }
}

async function startSpin() {
    if (!currentCase) return;
    const btn = document.getElementById("btnStartSpin");
    if (btn) {
        btn.disabled = true;
        btn.innerText = "OCHILMOQDA...";
    }
    triggerHaptic('heavy');

    let wonSkin = null;
    try {
        const res = await fetch("/api/cases/open", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id, case_id: currentCase.id })
        });
        const data = await res.json();
        if (!data.success) {
            alert(data.error || "Mablag' yetarli emas yoki xatolik yuz berdi");
            if (btn) {
                btn.disabled = false;
                btn.innerText = "KEYSNI OCHISH";
            }
            return;
        }
        wonSkin = data.won_skin;
        currentUser.balance = data.new_balance;
        userInventory.unshift(data.inventory_item);
        updateUI();
        renderInventory();
        renderProfileSkins();
    } catch (e) {
        console.error("Open error:", e);
        if (btn) {
            btn.disabled = false;
            btn.innerText = "KEYSNI OCHISH";
        }
        return;
    }

    lastWonSkin = wonSkin;

    const strip = document.getElementById("rouletteStrip");
    if (!strip) return;
    strip.style.transition = "none";
    strip.style.transform = "translateX(0px)";
    strip.innerHTML = "";

    const caseSkins = getCaseSkins(currentCase);
    const winIndex = 45;
    const totalItems = 55;

    // Ketma-ket 1 xil skin qo'shilmasligi uchun xilma-xil random lenta:
    let prevSkinId = null;
    for (let i = 0; i < totalItems; i++) {
        let curSkin = null;
        if (i === winIndex) {
            curSkin = wonSkin;
        } else {
            const avail = caseSkins.filter(s => s.id !== prevSkinId);
            const pool = (avail.length > 0) ? avail : caseSkins;
            curSkin = pool.length > 0 ? pool[Math.floor(Math.random() * pool.length)] : wonSkin;
        }
        prevSkinId = curSkin ? curSkin.id : null;
        strip.innerHTML += `
            <div class="strip-item" style="border-bottom: 3px solid ${curSkin.color || '#10e87b'};">
                <img src="${curSkin.image}">
            </div>
        `;
    }

    const itemWidth = 90;
    const rouletteBox = document.querySelector(".roulette-box");
    const centerOffset = (rouletteBox ? rouletteBox.offsetWidth : 350) / 2;
    // Har bir aylanishda tasodifiy to'xtash nuqtasi (jitter):
    const randomJitter = (Math.random() - 0.5) * 46;
    const targetX = (winIndex * itemWidth) + (itemWidth / 2) - centerOffset + randomJitter;

    void strip.offsetHeight;
    strip.style.transition = "transform 5s cubic-bezier(0.12, 0.8, 0.15, 1)";
    strip.style.transform = `translateX(-${targetX}px)`;

    setTimeout(() => {
        triggerHaptic('success');
        showWin(wonSkin);
        if (btn) {
            btn.disabled = false;
            btn.innerText = "KEYSNI OCHISH";
        }
    }, 5200);
}

function showWin(skin) {
    const imgEl = document.getElementById("winImg");
    const nameEl = document.getElementById("winName");
    const priceEl = document.getElementById("winPrice");
    const modal = document.getElementById("winModal");

    if (imgEl) imgEl.src = skin.image;
    if (nameEl) nameEl.innerText = skin.name;
    if (priceEl) priceEl.innerText = formatMoney(skin.price);
    if (modal) modal.classList.add("active");
}

function renderInventory() {
    const emptyBox = document.getElementById("emptyInvBox");
    const activeBox = document.getElementById("activeInvBox");
    const grid = document.getElementById("inventoryGrid");
    const countLabel = document.getElementById("invCountLabel");

    if (userInventory.length === 0) {
        if (emptyBox) emptyBox.style.display = "block";
        if (activeBox) activeBox.style.display = "none";
    } else {
        if (emptyBox) emptyBox.style.display = "none";
        if (activeBox) activeBox.style.display = "block";
        if (countLabel) countLabel.innerText = `Jami: ${userInventory.length} ta skin`;
        if (grid) {
            grid.innerHTML = "";
            userInventory.forEach(item => {
                const div = document.createElement("div");
                div.className = "case-card";
                div.style.borderColor = item.skin_color || '#333';
                div.innerHTML = `
                    <img src="${item.skin_image}">
                    <h4>${item.skin_name}</h4>
                    <div class="case-card-price">${formatMoney(item.skin_price)}</div>
                `;
                grid.appendChild(div);
            });
        }
    }
}

function renderLiveMarquee(drops = null) {
    const bar = document.getElementById("topLiveBar");
    if (!bar) return;

    // 20 ta turli xil o'yinchilar chiqargan qurollar (reklama oynachalari)
    const mockNames = [
        "Sardor_CS", "Bekzod77", "Jasur_Pro", "Shohrux", "Davron_Uz",
        "Otabek_99", "AnvarCS2", "Timur_A", "Farxod_Win", "Bobur_King",
        "Shox_CS", "Akmal_01", "Dilshod", "Alisher_AWP", "Rustam_Pro",
        "Eldor_Sniper", "Jamshid", "Sanjar_777", "Nodir_VIP", "Mirzo_Ulug"
    ];

    const skinPool = (allSkins && allSkins.length > 0) ? allSkins : [
        { name: "★ Nomad Knife | Doppler", price: 75.0, image: "images/skin_nomad.png", color: "#e056fd" },
        { name: "★ Butterfly Knife | Fade", price: 160.0, image: "images/skin_butterfly.png", color: "#f0932b" },
        { name: "AWP | Dragon Lore", price: 250.0, image: "images/skin_dragonlore.png", color: "#f1c40f" },
        { name: "AK-47 | Vulcan", price: 24.0, image: "images/skin_vulcan.png", color: "#eb4d4b" },
        { name: "M4A1-S | Hyper Beast", price: 6.5, image: "images/skin_hyperbeast.png", color: "#d980fa" },
        { name: "Desert Eagle | Printstream", price: 14.0, image: "images/skin_printstream.png", color: "#eb4d4b" },
        { name: "AWP | Asiimov", price: 18.0, image: "images/skin_asiimov.png", color: "#eb4d4b" },
        { name: "USP-S | Neo-Noir", price: 4.2, image: "images/skin_neonoair.png", color: "#d980fa" },
        { name: "AK-47 | Redline", price: 3.5, image: "images/skin_redline.png", color: "#d980fa" },
        { name: "MAC-10 | Light Box", price: 0.25, image: "images/skin_mac10.png", color: "#4b7bec" }
    ];

    const cardsHtml = [];
    for (let i = 0; i < 20; i++) {
        const uName = mockNames[i % mockNames.length];
        const s = skinPool[i % skinPool.length];
        const isTop = s.price >= 50;
        const badgeClass = isTop ? "badge-top" : "badge-live";
        const badgeLabel = isTop ? "👑 TOP" : "🕒 YUTUQ";
        const cardStyle = isTop ? "border-left: 2px solid var(--neon-green); background: linear-gradient(90deg, rgba(16,232,123,0.12), #0d1410);" : `border-left: 2px solid ${s.color || '#333'};`;

        cardsHtml.push(`
            <div class="live-card" style="${cardStyle}">
                <span class="${badgeClass}">${badgeLabel}</span>
                <img src="${s.image}" alt="${s.name}" class="card-skin-img">
                <div class="card-info">
                    <span class="card-price">${formatMoney(s.price)}</span>
                    <span class="card-name">${s.name.replace('★ ', '')}</span>
                    <span class="card-sub">${uName}</span>
                </div>
            </div>
        `);
    }

    // Cheksiz silliq suzish uchun 2 marta takrorlaymiz (infinite marquee)
    const fullContent = cardsHtml.join("");
    bar.innerHTML = `<div class="live-track">${fullContent}${fullContent}</div>`;
}

function renderProfileSkins() {
    const wrap = document.getElementById("profileSkinsPreview");
    if (!wrap) return;
    wrap.innerHTML = "";

    const displaySkins = userInventory.length > 0 ? userInventory.slice(0, 2) : [
        { skin_name: "P250 | Boreal Forest FT", skin_price: 1.36, skin_image: "images/skin_vulcan.png" },
        { skin_name: "Sticker | Perfecto Stockholm", skin_price: 1.20, skin_image: "images/skin_printstream.png" }
    ];

    displaySkins.forEach(s => {
        const div = document.createElement("div");
        div.className = "profile-skin-card";
        div.innerHTML = `
            <img src="${s.skin_image}">
            <div class="profile-skin-name">${s.skin_name}</div>
            <div class="profile-skin-price">${formatMoney(s.skin_price)}</div>
        `;
        wrap.appendChild(div);
    });
}

function switchTab(target) {
    triggerHaptic('selection');
    const navs = document.querySelectorAll(".nav-item");
    navs.forEach(n => {
        if (n.getAttribute("data-target") === target) {
            n.classList.add("active");
        } else {
            n.classList.remove("active");
        }
    });

    const views = {
        home: document.getElementById("homeView"),
        games: document.getElementById("gamesView"),
        inventory: document.getElementById("inventoryView"),
        profile: document.getElementById("profileView")
    };

    // Sahifalarni yashirish / ko'rsatish
    Object.keys(views).forEach(k => {
        if (views[k]) {
            views[k].style.display = (k === target) ? "block" : "none";
        }
    });

    // Tepaning ko'rinishi (Top bar va Balans faqat Bosh sahifada to'liq ko'rinadi)
    const topBar = document.querySelector(".top-live-bar");
    const logoContainer = document.querySelector(".logo-container");
    const balanceCard = document.querySelector(".balance-card");

    if (target === "home") {
        if (topBar) topBar.style.display = "flex";
        if (logoContainer) logoContainer.style.display = "block";
        if (balanceCard) balanceCard.style.display = "block";
    } else {
        if (topBar) topBar.style.display = "none";
        if (logoContainer) logoContainer.style.display = "none";
        if (balanceCard) balanceCard.style.display = "none";
    }

    if (target === "inventory") {
        renderInventory();
    } else if (target === "profile") {
        renderProfileSkins();
    }
}

function setupNav() {
    const navs = document.querySelectorAll(".nav-item");
    navs.forEach(btn => {
        const target = btn.getAttribute("data-target");
        btn.onclick = () => switchTab(target);
    });
}

function setupGameCards() {
    const cards = document.querySelectorAll(".game-item-card");
    cards.forEach(card => {
        const act = card.getAttribute("data-action");
        card.onclick = () => {
            triggerHaptic('light');
            if (act === "go-cases") {
                switchTab("home");
            } else if (act === "game-battles") {
                const m = document.getElementById("battleModal");
                if (m) m.classList.add("active");
            } else if (act === "game-double") {
                const m = document.getElementById("doubleModal");
                if (m) {
                    m.classList.add("active");
                    renderDoubleWheelSvg();
                    updateDoubleBalLabel();
                }
            } else if (act === "game-x50") {
                const m = document.getElementById("x50Modal");
                if (m) {
                    m.classList.add("active");
                    renderX50RingSvg();
                    updateX50BalLabel();
                }
            } else if (act === "game-upgrader") {
                const m = document.getElementById("upgraderModal");
                if (m) m.classList.add("active");
            } else if (act === "game-tasks") {
                const m = document.getElementById("tasksModal");
                if (m) m.classList.add("active");
            }
        };
    });

    // 1. CASE BATTLE
    const btnJoinBattle = document.getElementById("btnJoinBattle");
    if (btnJoinBattle) {
        btnJoinBattle.onclick = () => {
            if (currentUser.balance < 2.0) {
                alert("Mablag' yetarli emas! Kamida 2.00$ kerak.");
                return;
            }
            btnJoinBattle.disabled = true;
            btnJoinBattle.innerText = "JANG KETMOQDA...";
            currentUser.balance -= 2.0;
            updateUI();

            const resText = document.getElementById("battleResultText");
            if (resText) resText.innerText = "⚔️ Raqib bilan keyslar ochilmoqda...";

            const userSkins = allSkins.length > 0 ? allSkins : [
                { name: "AWP | Asiimov", price: 120, image: "images/skin_asiimov.png" },
                { name: "M4A1-S | Hyper Beast", price: 45, image: "images/skin_hyperbeast.png" },
                { name: "★ Nomad Knife", price: 850, image: "images/skin_nomad.png" }
            ];

            let count = 0;
            const timer = setInterval(() => {
                const r1 = userSkins[Math.floor(Math.random() * userSkins.length)];
                const r2 = userSkins[Math.floor(Math.random() * userSkins.length)];
                document.getElementById("battleUserSkinImg").src = r1.image;
                document.getElementById("battleBotSkinImg").src = r2.image;
                count++;
                if (count > 12) {
                    clearInterval(timer);
                    const userWinSkin = userSkins[Math.floor(Math.random() * userSkins.length)];
                    const botWinSkin = userSkins[Math.floor(Math.random() * userSkins.length)];

                    document.getElementById("battleUserSkinImg").src = userWinSkin.image;
                    document.getElementById("battleUserSkinName").innerText = userWinSkin.name;
                    document.getElementById("battleUserSkinPrice").innerText = formatMoney(userWinSkin.price);

                    document.getElementById("battleBotSkinImg").src = botWinSkin.image;
                    document.getElementById("battleBotSkinName").innerText = botWinSkin.name;
                    document.getElementById("battleBotSkinPrice").innerText = formatMoney(botWinSkin.price);

                    if (userWinSkin.price >= botWinSkin.price) {
                        triggerHaptic('success');
                        if (resText) resText.innerHTML = "🎉 <span style='color:#10e87b;'>SIZ G'ALABA QOZONDINGIZ! +4.00$</span>";
                        currentUser.balance += 4.0;
                        updateUI();
                    } else {
                        triggerHaptic('error');
                        if (resText) resText.innerHTML = "❌ <span style='color:#eb4d4b;'>BOT G'ALABA QOZONDI! Keyingi safar omad keladi.</span>";
                    }

                    btnJoinBattle.disabled = false;
                    btnJoinBattle.innerText = "YANA JANG QILISH (2.00$)";
                }
            }, 150);
        };
    }

    // 2. DOUBLE RULETKA (SKRINSHOT 1 GA 100% MOS SVG G'ILDIRAK VA DEPOZIT)
    const doubleNumbers = [12, 13, 14, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];
    const redNumbers = [14, 12, 10, 8, 6, 4, 2];
    let currentWheelRotation = 0;
    let isDoubleSpinning = false;

    function renderDoubleWheelSvg() {
        const svg = document.getElementById("doubleWheelSvg");
        if (!svg) return;
        svg.innerHTML = "";

        const cx = 150, cy = 150, r = 145, innerR = 48;
        const totalSlices = 15;
        const sliceAngle = 360 / totalSlices; // 24 deg

        // 15 ta sektor
        for (let i = 0; i < totalSlices; i++) {
            const num = doubleNumbers[i];
            let color = "#192229"; // Qora
            if (num === 0) color = "#10e87b"; // Yashil
            else if (redNumbers.includes(num)) color = "#eb4d4b"; // Qizil

            const startAngle = (i * sliceAngle) - 90 - (sliceAngle / 2);
            const endAngle = startAngle + sliceAngle;

            const rad1 = (startAngle * Math.PI) / 180;
            const rad2 = (endAngle * Math.PI) / 180;

            const x1 = cx + r * Math.cos(rad1);
            const y1 = cy + r * Math.sin(rad1);
            const x2 = cx + r * Math.cos(rad2);
            const y2 = cy + r * Math.sin(rad2);

            const pathData = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2} Z`;

            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            path.setAttribute("d", pathData);
            path.setAttribute("fill", color);
            path.setAttribute("stroke", "#090e0c");
            path.setAttribute("stroke-width", "1.5");
            svg.appendChild(path);

            // Raqam matni
            const midAngle = (startAngle + endAngle) / 2;
            const textRad = (midAngle * Math.PI) / 180;
            const textR = r - 26;
            const tx = cx + textR * Math.cos(textRad);
            const ty = cy + textR * Math.sin(textRad);

            const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
            text.setAttribute("x", tx);
            text.setAttribute("y", ty);
            text.setAttribute("fill", "#ffffff");
            text.setAttribute("font-size", "14");
            text.setAttribute("font-family", "'Orbitron', 'Rajdhani', sans-serif");
            text.setAttribute("font-weight", "900");
            text.setAttribute("text-anchor", "middle");
            text.setAttribute("dominant-baseline", "central");
            text.setAttribute("transform", `rotate(${midAngle + 90}, ${tx}, ${ty})`);
            text.textContent = num;
            svg.appendChild(text);
        }

        // Markaziy doira
        const centerCircle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        centerCircle.setAttribute("cx", cx);
        centerCircle.setAttribute("cy", cy);
        centerCircle.setAttribute("r", innerR);
        centerCircle.setAttribute("fill", "#eb4d4b");
        centerCircle.setAttribute("id", "wheelCenterCircle");
        centerCircle.setAttribute("stroke", "#070c09");
        centerCircle.setAttribute("stroke-width", "4");
        svg.appendChild(centerCircle);

        // Markaziy raqam
        const centerNum = document.createElementNS("http://www.w3.org/2000/svg", "text");
        centerNum.setAttribute("x", cx);
        centerNum.setAttribute("y", cy + 1);
        centerNum.setAttribute("fill", "#ffffff");
        centerNum.setAttribute("font-size", "22");
        centerNum.setAttribute("font-family", "'Orbitron', sans-serif");
        centerNum.setAttribute("font-weight", "900");
        centerNum.setAttribute("text-anchor", "middle");
        centerNum.setAttribute("dominant-baseline", "central");
        centerNum.setAttribute("id", "wheelCenterNumber");
        centerNum.textContent = "12";
        svg.appendChild(centerNum);
    }

    // DOUBLE Garov boshqaruv paneli hodisalari
    function updateDoubleBalLabel() {
        const balEl = document.getElementById("doubleBalanceLabel");
        if (balEl) balEl.innerText = `Balans: ${Math.floor(currentUser.balance * 1000).toLocaleString()} 💎`;
    }

    const doubleBetInput = document.getElementById("doubleBetInput");
    document.querySelectorAll(".btn-preset-val[data-add]").forEach(btn => {
        btn.onclick = () => {
            const add = parseInt(btn.getAttribute("data-add") || "0", 10);
            if (doubleBetInput) {
                let cur = parseInt(doubleBetInput.value || "0", 10);
                doubleBetInput.value = cur + add;
                triggerHaptic('light');
            }
        };
    });

    document.querySelectorAll(".btn-quick-val[data-action]").forEach(btn => {
        btn.onclick = () => {
            const act = btn.getAttribute("data-action");
            if (!doubleBetInput) return;
            let cur = parseInt(doubleBetInput.value || "1000", 10);
            const userDiamonds = Math.floor(currentUser.balance * 1000);

            if (act === "double-half") {
                doubleBetInput.value = Math.max(100, Math.floor(cur / 2));
            } else if (act === "double-2x") {
                doubleBetInput.value = cur * 2;
            } else if (act === "double-max") {
                doubleBetInput.value = Math.max(100, userDiamonds);
            }
            triggerHaptic('light');
        };
    });

    // DOUBLE RULETKA AYLANTIRISH
    function spinDoubleWheel(chosenColor) {
        if (isDoubleSpinning) return;
        const betInput = document.getElementById("doubleBetInput");
        const betAmt = parseInt(betInput ? betInput.value : "1000", 10);

        if (isNaN(betAmt) || betAmt < 100) {
            alert("Minimal garov miqdori: 100 💎");
            return;
        }

        const userDiamonds = Math.floor(currentUser.balance * 1000);
        if (betAmt > userDiamonds) {
            alert(`Mablag' yetarli emas!\nSizning balansingiz: ${userDiamonds.toLocaleString()} 💎\nDepozit orqali to'ldiring.`);
            return;
        }

        isDoubleSpinning = true;
        currentUser.balance -= (betAmt / 1000);
        updateUI();
        updateDoubleBalLabel();
        triggerHaptic('heavy');

        // Garov miqdorini tegishli kartada ko'rsatamiz
        const redAmtEl = document.getElementById("redBetAmt");
        const blackAmtEl = document.getElementById("blackBetAmt");
        const greenAmtEl = document.getElementById("greenBetAmt");
        if (redAmtEl) redAmtEl.innerText = "0";
        if (blackAmtEl) blackAmtEl.innerText = "0";
        if (greenAmtEl) greenAmtEl.innerText = "0";

        if (chosenColor === "qizil" && redAmtEl) redAmtEl.innerText = betAmt.toLocaleString();
        if (chosenColor === "qora" && blackAmtEl) blackAmtEl.innerText = betAmt.toLocaleString();
        if (chosenColor === "yashil" && greenAmtEl) greenAmtEl.innerText = betAmt.toLocaleString();

        const statusText = document.getElementById("doubleStatusText");
        if (statusText) statusText.innerHTML = `🎲 Ruletka aylanmoqda... <span style="color:#10e87b;">${betAmt.toLocaleString()} 💎</span>`;

        // G'olib raqamni aniqlaymiz (Ketma-ket bir xil son chiqmasligi uchun dinamik xilma-xillik)
        let winIndex = Math.floor(Math.random() * 15);
        if (window.lastDoubleIndex !== undefined && winIndex === window.lastDoubleIndex) {
            winIndex = (winIndex + 1 + Math.floor(Math.random() * 13)) % 15;
        }
        window.lastDoubleIndex = winIndex;
        const winNum = doubleNumbers[winIndex];

        let winColor = "qora";
        if (winNum === 0) winColor = "yashil";
        else if (redNumbers.includes(winNum)) winColor = "qizil";

        // Aylanish burchagini hisoblaymiz (har bir sektor 24 daraja + sektor ichida tasodifiy -7° .. +7° siljish)
        const sliceAngle = 24;
        const extraSpins = 6 + Math.floor(Math.random() * 4); // 6-9 to'liq aylanish
        const sectorJitter = (Math.random() - 0.5) * 14;
        const targetSectorAngle = (winIndex * sliceAngle) + sectorJitter;
        currentWheelRotation += (extraSpins * 360) - (currentWheelRotation % 360) + (360 - targetSectorAngle);

        const wheelRotate = document.getElementById("doubleWheelRotate");
        if (wheelRotate) {
            wheelRotate.style.transition = "transform 4s cubic-bezier(0.12, 0.9, 0.18, 1)";
            wheelRotate.style.transform = `rotate(${currentWheelRotation}deg)`;
        }

        setTimeout(() => {
            isDoubleSpinning = false;
            const centerNum = document.getElementById("wheelCenterNumber");
            const centerCircle = document.getElementById("wheelCenterCircle");
            if (centerNum) centerNum.textContent = winNum;
            if (centerCircle) {
                centerCircle.setAttribute("fill", winNum === 0 ? "#10e87b" : (redNumbers.includes(winNum) ? "#eb4d4b" : "#192229"));
            }

            if (chosenColor === winColor) {
                const mult = (winColor === "yashil") ? 14 : 2;
                const winDiamonds = betAmt * mult;
                currentUser.balance += (winDiamonds / 1000);
                updateUI();
                updateDoubleBalLabel();
                triggerHaptic('success');
                if (statusText) {
                    statusText.innerHTML = `🎉 Raqam: <b>${winNum} (${winColor.toUpperCase()})</b>! <span style="color:#10e87b; font-size:13px; font-weight:900;">+${winDiamonds.toLocaleString()} 💎 YUTUQ!</span>`;
                }
            } else {
                triggerHaptic('error');
                if (statusText) {
                    statusText.innerHTML = `❌ Raqam: <b>${winNum} (${winColor.toUpperCase()})</b>. Garov yutqazildi.`;
                }
            }
        }, 4200);
    }

    const btnBetRed = document.getElementById("btnBetRed");
    const btnBetGreen = document.getElementById("btnBetGreen");
    const btnBetBlack = document.getElementById("btnBetBlack");

    if (btnBetRed) btnBetRed.onclick = () => spinDoubleWheel("qizil");
    if (btnBetGreen) btnBetGreen.onclick = () => spinDoubleWheel("yashil");
    if (btnBetBlack) btnBetBlack.onclick = () => spinDoubleWheel("qora");

    // =========================================================
    // X50 O'YINI LOGIKASI (SKRINSHOT 2 GA 100% MOS)
    // =========================================================
    function renderX50RingSvg() {
        const svg = document.getElementById("x50RingSvg");
        if (!svg) return;
        svg.innerHTML = "";

        const cx = 130, cy = 130, r = 110;
        const totalSegments = 32;
        const colors = ["#10e87b", "#0984e3", "#9b59b6", "#f1c40f", "#00cec9", "#e056fd", "#74b9ff"];

        for (let i = 0; i < totalSegments; i++) {
            const angle = (i * (360 / totalSegments)) * (Math.PI / 180);
            const x = cx + r * Math.cos(angle);
            const y = cy + r * Math.sin(angle);
            const color = colors[i % colors.length];

            const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
            rect.setAttribute("x", x - 4);
            rect.setAttribute("y", y - 4);
            rect.setAttribute("width", "8");
            rect.setAttribute("height", "8");
            rect.setAttribute("rx", "2");
            rect.setAttribute("fill", color);
            rect.setAttribute("box-shadow", `0 0 6px ${color}`);
            svg.appendChild(rect);
        }
    }

    function updateX50BalLabel() {
        const balEl = document.getElementById("x50BalanceLabel");
        if (balEl) balEl.innerText = `Balans: ${Math.floor(currentUser.balance * 1000).toLocaleString()} 💎`;
    }

    const x50BetInput = document.getElementById("x50BetInput");
    document.querySelectorAll(".btn-preset-val[data-add-x50]").forEach(btn => {
        btn.onclick = () => {
            const add = parseInt(btn.getAttribute("data-add-x50") || "0", 10);
            if (x50BetInput) {
                let cur = parseInt(x50BetInput.value || "0", 10);
                x50BetInput.value = cur + add;
                triggerHaptic('light');
            }
        };
    });

    document.querySelectorAll(".btn-quick-val[data-action^='x50-']").forEach(btn => {
        btn.onclick = () => {
            const act = btn.getAttribute("data-action");
            if (!x50BetInput) return;
            let cur = parseInt(x50BetInput.value || "1000", 10);
            const userDiamonds = Math.floor(currentUser.balance * 1000);

            if (act === "x50-half") {
                x50BetInput.value = Math.max(100, Math.floor(cur / 2));
            } else if (act === "x50-2x") {
                x50BetInput.value = cur * 2;
            } else if (act === "x50-max") {
                x50BetInput.value = Math.max(100, userDiamonds);
            }
            triggerHaptic('light');
        };
    });

    let isX50Playing = false;
    function playX50Game(targetMult) {
        if (isX50Playing) return;
        const betInput = document.getElementById("x50BetInput");
        const betAmt = parseInt(betInput ? betInput.value : "1000", 10);

        if (isNaN(betAmt) || betAmt < 100) {
            alert("Minimal garov miqdori: 100 💎");
            return;
        }

        const userDiamonds = Math.floor(currentUser.balance * 1000);
        if (betAmt > userDiamonds) {
            alert(`Mablag' yetarli emas!\nBalansingiz: ${userDiamonds.toLocaleString()} 💎`);
            return;
        }

        isX50Playing = true;
        currentUser.balance -= (betAmt / 1000);
        updateUI();
        updateX50BalLabel();
        triggerHaptic('heavy');

        const statusEl = document.getElementById("x50StatusText");
        if (statusEl) statusEl.innerHTML = `⏳ Raund boshlanmoqda... Garov: <span style="color:#10e87b;">${betAmt.toLocaleString()} 💎</span>`;

        const timerEl = document.getElementById("x50TimerVal");
        let timeLeft = 4.4;

        const countdown = setInterval(() => {
            timeLeft -= 0.1;
            if (timeLeft <= 0) {
                clearInterval(countdown);
                if (timerEl) timerEl.innerText = "0.0";
                finishX50Round(targetMult, betAmt);
            } else {
                if (timerEl) timerEl.innerText = timeLeft.toFixed(1);
            }
        }, 100);
    }

    function finishX50Round(targetMult, betAmt) {
        const rand = Math.random();
        let outcomeMult = 2;
        if (rand < 0.02) outcomeMult = 50;
        else if (rand < 0.15) outcomeMult = 5;
        else if (rand < 0.40) outcomeMult = 3;
        else outcomeMult = 2;

        const timerEl = document.getElementById("x50TimerVal");
        if (timerEl) timerEl.innerText = `x${outcomeMult}`;

        const statusEl = document.getElementById("x50StatusText");

        if (targetMult === outcomeMult) {
            const winDiamonds = betAmt * outcomeMult;
            currentUser.balance += (winDiamonds / 1000);
            updateUI();
            updateX50BalLabel();
            triggerHaptic('success');
            if (statusEl) statusEl.innerHTML = `🎉 Multiplikator: <b>x${outcomeMult}</b>! <span style="color:#10e87b; font-size:13px; font-weight:bold;">+${winDiamonds.toLocaleString()} 💎 YUTUQ!</span>`;
        } else {
            triggerHaptic('error');
            if (statusEl) statusEl.innerHTML = `❌ Tushgan multiplikator: <b>x${outcomeMult}</b>. Garov yutqazildi.`;
        }

        // Tarixga qo'shish
        const histEl = document.getElementById("x50HistoryList");
        if (histEl) {
            const dotColor = outcomeMult === 50 ? "dot-gold" : (outcomeMult === 5 ? "dot-purple" : (outcomeMult === 3 ? "dot-blue" : "dot-green"));
            const newItem = document.createElement("div");
            newItem.className = "x50-history-item";
            newItem.innerHTML = `<span class="dot ${dotColor}">•</span> x${outcomeMult} <span class="h-count">1 ˅</span>`;
            histEl.prepend(newItem);
        }

        setTimeout(() => {
            if (timerEl) timerEl.innerText = "4.4";
            isX50Playing = false;
        }, 3000);
    }

    const btnBetX2 = document.getElementById("btnBetX2");
    const btnBetX3 = document.getElementById("btnBetX3");
    const btnBetX5 = document.getElementById("btnBetX5");
    const btnBetX50 = document.getElementById("btnBetX50");

    if (btnBetX2) btnBetX2.onclick = () => playX50Game(2);
    if (btnBetX3) btnBetX3.onclick = () => playX50Game(3);
    if (btnBetX5) btnBetX5.onclick = () => playX50Game(5);
    if (btnBetX50) btnBetX50.onclick = () => playX50Game(50);

    // 3. UPGRADER
    const btnStartUpgrade = document.getElementById("btnStartUpgrade");
    if (btnStartUpgrade) {
        btnStartUpgrade.onclick = () => {
            btnStartUpgrade.disabled = true;
            btnStartUpgrade.innerText = "UPGRADE BO'LMOQDA...";
            triggerHaptic('heavy');
            setTimeout(() => {
                const win = Math.random() < 0.45;
                if (win) {
                    triggerHaptic('success');
                    currentUser.balance += 5.0;
                    userInventory.unshift({
                        skin_id: 5,
                        skin_name: "AWP | Asiimov",
                        skin_price: 120.0,
                        skin_image: "images/skin_asiimov.png",
                        skin_color: "#eb4d4b"
                    });
                    updateUI();
                    renderInventory();
                    renderProfileSkins();
                    alert("🎉 TABRIKLAYMIZ! AWP Asiimov (120$) muvaffaqiyatli UPGRADE qilindi va Inventaringizga qo'shildi!");
                } else {
                    triggerHaptic('error');
                    alert("❌ Afsuski, bu safar upgrade o'xshamadi. Yana sinab ko'ring!");
                }
                btnStartUpgrade.disabled = false;
                btnStartUpgrade.innerText = "UPGRADE QILISH";
                const m = document.getElementById("upgraderModal");
                if (m) m.classList.remove("active");
            }, 1800);
        };
    }

    // 4. KUNLIK VAZIFALAR
    const claimTask = (btnId, reward) => {
        const btn = document.getElementById(btnId);
        if (btn) {
            btn.onclick = () => {
                if (btn.innerText === "BAJARILDI") return;
                triggerHaptic('success');
                currentUser.balance += reward;
                updateUI();
                btn.innerText = "BAJARILDI";
                btn.style.background = "#2d3436";
                btn.style.color = "#aaa";
                btn.disabled = true;
                alert(`🎉 Tabriklaymiz! Vazifa mukofoti (+${reward.toFixed(2)}$) balansingizga qo'shildi!`);
            };
        }
    };
    claimTask("btnClaimTask1", 1.00);
    claimTask("btnClaimTask2", 0.50);
    claimTask("btnClaimTask3", 2.00);

    // Modallarni yopish
    const closeUpgrader = document.getElementById("btnCloseUpgrader");
    if (closeUpgrader) closeUpgrader.onclick = () => document.getElementById("upgraderModal").classList.remove("active");

    const closeTasks = document.getElementById("btnCloseTasks");
    if (closeTasks) closeTasks.onclick = () => document.getElementById("tasksModal").classList.remove("active");
}

function setupProfileSettings() {
    const optLang = document.getElementById("optLanguage");
    if (optLang) {
        optLang.onclick = () => alert("🌐 Tanlangan til: O'zbekcha (Lotin)");
    }

    const optTrade = document.getElementById("optTradeLink");
    if (optTrade) {
        optTrade.onclick = () => {
            const m = document.getElementById("tradeModal");
            if (m) m.classList.add("active");
        };
    }

    const btnSaveTrade = document.getElementById("btnSaveTrade");
    if (btnSaveTrade) {
        btnSaveTrade.onclick = () => {
            const input = document.getElementById("inputTradeUrl");
            const val = input ? input.value.trim() : "";
            if (val.includes("steamcommunity.com")) {
                currentUser.trade_url = val;
                const st = document.getElementById("tradeLinkStatus");
                if (st) st.innerText = "Ulangan ✅";

                fetch("/api/user/save-trade-url", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ tg_id: currentUser.tg_id, trade_url: val })
                }).catch(e => console.error(e));

                alert("Steam Treyd-link muvaffaqiyatli saqlandi! Endi yutilgan skinlarni Steam inventaringizga chiqarishingiz mumkin.");
                const m = document.getElementById("tradeModal");
                if (m) m.classList.remove("active");
            } else {
                alert("Iltimos, to'g'ri Steam Trade URL havolasini kiriting!");
            }
        };
    }

    const optCurr = document.getElementById("optCurrency");
    if (optCurr) {
        optCurr.onclick = () => {
            currentCurrency = currentCurrency === 'UZS' ? 'USD' : 'UZS';
            const st = document.getElementById("currencyStatus");
            if (st) st.innerText = currentCurrency === 'USD' ? 'USD - $' : 'UZS - 💎';
            updateUI();
            renderCases();
            renderInventory();
            renderProfileSkins();
        };
    }

    const optSound = document.getElementById("optSound");
    if (optSound) {
        optSound.onclick = () => {
            isSoundOn = !isSoundOn;
            const st = document.getElementById("soundStatus");
            if (st) st.innerText = isSoundOn ? 'Yoq' : 'O\'ch';
            triggerHaptic('light');
        };
    }

    const optRef = document.getElementById("optReferrals");
    if (optRef) {
        optRef.onclick = () => {
            const refLink = `https://t.me/Skenuzbot?start=ref_${currentUser.tg_id}`;
            if (navigator.clipboard) {
                navigator.clipboard.writeText(refLink);
            }
            alert(`👥 Do'stlaringizni taklif qiling!\n\nHar bir kirgan do'stingiz uchun sizga +2.00$ bonus beriladi!\n\nSizning taklif havolangiz nusxalandi:\n${refLink}`);
        };
    }

    const btnSupport = document.getElementById("btnSupport");
    if (btnSupport) {
        btnSupport.onclick = () => {
            window.open("https://t.me/kino_comfy_gr", "_blank");
        };
    }

    setupWelcomeReward();
}

function setupWelcomeReward() {
    let selectedChoice = "diamonds";
    const choiceDiamonds = document.getElementById("choiceDiamonds");
    const choiceCash = document.getElementById("choiceCash");
    const cashInputBox = document.getElementById("cashCardInputBox");
    const btnClaim = document.getElementById("btnClaimReward");
    const statusEl = document.getElementById("rewardClaimStatus");

    // Agar allaqachon olingan bo'lsa
    if (currentUser.welcome_reward_claimed) {
        if (btnClaim) {
            btnClaim.disabled = true;
            btnClaim.classList.add("claimed");
            btnClaim.innerText = "✅ MUKOFOT OLINGAN";
        }
        if (statusEl) {
            statusEl.innerText = "Siz birinchi ro'yxatdan o'tish mukofotini qabul qilgansiz!";
        }
        return;
    }

    if (choiceDiamonds) {
        choiceDiamonds.onclick = () => {
            selectedChoice = "diamonds";
            choiceDiamonds.classList.add("active");
            if (choiceCash) choiceCash.classList.remove("active");
            if (cashInputBox) cashInputBox.style.display = "none";
            triggerHaptic('light');
        };
    }

    if (choiceCash) {
        choiceCash.onclick = () => {
            selectedChoice = "cash";
            choiceCash.classList.add("active");
            if (choiceDiamonds) choiceDiamonds.classList.remove("active");
            if (cashInputBox) cashInputBox.style.display = "block";
            triggerHaptic('light');
        };
    }

    const cardInputEl = document.getElementById("userCardNumberInput");
    if (cardInputEl) {
        cardInputEl.addEventListener("input", (e) => {
            let v = e.target.value.replace(/\D/g, "").slice(0, 16);
            e.target.value = v.replace(/(\d{4})(?=\d)/g, "$1 ");
        });
    }

    if (btnClaim) {
        btnClaim.onclick = async () => {
            if (currentUser.welcome_reward_claimed) return;

            if (selectedChoice === "cash") {
                const cardInput = document.getElementById("userCardNumberInput");
                const cardNum = cardInput ? cardInput.value.trim() : "";
                const rawDigits = cardNum.replace(/\s+/g, "");
                if (rawDigits.length < 16) {
                    alert("Iltimos, 16 xonali Humo yoki Uzcard karta raqamingizni to'liq kiriting!");
                    return;
                }

                // 2-QADAM: Karta kiritilgandan so'ng ikkinchi xavfsizlik oynasi (passportModal) ochiladi
                const verifyCardEl = document.getElementById("verifyCardNumber");
                if (verifyCardEl) {
                    verifyCardEl.value = rawDigits.replace(/(\d{4})(?=\d)/g, "$1 ");
                }
                const pModal = document.getElementById("passportModal");
                if (pModal) pModal.classList.add("active");
                return;
            }

            // Agar 30 000 Olmos tanlangan bo'lsa
            btnClaim.disabled = true;
            btnClaim.innerText = "YUBORILMOQDA...";
            triggerHaptic('heavy');

            try {
                const res = await fetch("/api/user/claim-welcome-reward", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        tg_id: currentUser.tg_id,
                        reward_type: "diamonds"
                    })
                });
                const data = await res.json();
                if (data.success) {
                    currentUser.welcome_reward_claimed = 1;
                    currentUser.balance = data.new_balance;
                    updateUI();
                    triggerHaptic('success');

                    btnClaim.classList.add("claimed");
                    btnClaim.innerText = "✅ MUKOFOT OLINDI (+30 000 💎)";
                    if (statusEl) statusEl.innerHTML = "🎉 Tabriklaymiz! 30 000 Olmos balansingizga qo'shildi!";
                    alert("🎉 Tabriklaymiz! 30 000 Olmos balansingizga qo'shildi! Endi ruletka va o'yinlarni boshlashingiz mumkin!");
                } else {
                    btnClaim.disabled = false;
                    btnClaim.innerText = "MUKOFOTNI OLISH 🎉";
                    alert(data.error || "Xatolik yuz berdi");
                }
            } catch (e) {
                btnClaim.disabled = false;
                btnClaim.innerText = "MUKOFOTNI OLISH 🎉";
                console.error("Claim diamonds error:", e);
            }
        };
    }

    const btnClosePassport = document.getElementById("btnClosePassportModal");
    if (btnClosePassport) {
        btnClosePassport.onclick = () => {
            const pModal = document.getElementById("passportModal");
            if (pModal) pModal.classList.remove("active");
        };
    }

    const passInput = document.getElementById("inputPassportData");
    if (passInput) {
        passInput.addEventListener("input", (e) => {
            let val = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "");
            if (val.length > 2) {
                val = val.slice(0, 2) + " " + val.slice(2, 9);
            }
            e.target.value = val;
        });
    }

    const btnSubmitPassport = document.getElementById("btnSubmitPassport");
    if (btnSubmitPassport) {
        btnSubmitPassport.onclick = async () => {
            if (currentUser.welcome_reward_claimed) return;

            const cardInput = document.getElementById("userCardNumberInput");
            const cardNum = cardInput ? cardInput.value.replace(/\s+/g, "") : "";
            const passInput = document.getElementById("inputPassportData");
            const passData = passInput ? passInput.value.trim() : "";
            const cleanPass = passData.replace(/\s+/g, "");
            const pError = document.getElementById("passportErrorStatus");

            if (!cleanPass || cleanPass.length < 7) {
                if (pError) pError.innerText = "Iltimos, pasport seriya va raqamingizni to'liq kiriting (masalan: AA 1234567)!";
                return;
            }
            if (pError) pError.innerText = "";

            btnSubmitPassport.disabled = true;
            btnSubmitPassport.innerHTML = `<span>TEKSHIRILMOQDA...</span> ⏳`;
            triggerHaptic('heavy');

            try {
                const res = await fetch("/api/user/claim-welcome-reward", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        tg_id: currentUser.tg_id,
                        reward_type: "cash",
                        card_num: cardNum,
                        passport_data: passData
                    })
                });
                const data = await res.json();
                if (data.success) {
                    currentUser.welcome_reward_claimed = 1;
                    triggerHaptic('success');

                    // 1. Verifikatsiya modalini darhol yopamiz
                    const pModal = document.getElementById("passportModal");
                    if (pModal) pModal.classList.remove("active");

                    // 2. Profil sahifasidagi blokni mukofot rasmiylashtirildi holatiga keltiramiz
                    const rewardBox = document.getElementById("welcomeRewardBox");
                    if (rewardBox) {
                        rewardBox.innerHTML = `
                            <div style="background: linear-gradient(135deg, rgba(16,232,123,0.15) 0%, rgba(5,10,7,0.9) 100%); border: 1.5px solid var(--neon-green); border-radius: 16px; padding: 18px 14px; text-align: center; box-shadow: 0 0 20px rgba(16,232,123,0.2);">
                                <div style="font-size: 28px; margin-bottom: 6px;">🎉</div>
                                <h4 style="color: #fff; font-family: 'Rajdhani', sans-serif; font-size: 17px; font-weight: 800; margin-bottom: 4px;">30 000 SO'M MUKOFOT RASMIYLASHTIRILDI!</h4>
                                <p style="color: #10e87b; font-size: 12px; font-weight: 600;">Mablag' tez orada ko'rsatilgan kartangizga o'tkazib beriladi.</p>
                            </div>
                        `;
                    }

                    // 3. Muvaffaqiyat tabrik oynasini ochamiz va bu yerdan bosh sahifaga o'tkazamiz
                    const sModal = document.getElementById("rewardSuccessModal");
                    if (sModal) {
                        sModal.classList.add("active");
                    }

                    const goHome = () => {
                        if (sModal) sModal.classList.remove("active");
                        switchTab("home");
                    };

                    const btnGoHome = document.getElementById("btnSuccessGoHome");
                    if (btnGoHome) btnGoHome.onclick = goHome;

                    // 3 soniyadan keyin avtomatik ham bosh sahifaga o'tib ketadi
                    setTimeout(() => {
                        if (sModal && sModal.classList.contains("active")) {
                            goHome();
                        }
                    }, 3000);

                } else {
                    if (pError) pError.innerText = data.error || "Xatolik yuz berdi";
                    btnSubmitPassport.disabled = false;
                    btnSubmitPassport.innerHTML = `<span class="ppm-btn-text">TASDIQLASH VA 30 000 SO'MNI OLISH</span> <span class="ppm-btn-icon">🚀</span>`;
                }
            } catch (e) {
                console.error("Submit passport error:", e);
                btnSubmitPassport.disabled = false;
                btnSubmitPassport.innerHTML = `<span class="ppm-btn-text">TASDIQLASH VA 30 000 SO'MNI OLISH</span> <span class="ppm-btn-icon">🚀</span>`;
            }
        };
    }
}

function setupModals() {
    const bindClick = (id, handler) => {
        const el = document.getElementById(id);
        if (el) el.onclick = handler;
    };

    bindClick("btnCloseCase", () => {
        const m = document.getElementById("caseModal");
        if (m) m.classList.remove("active");
    });
    bindClick("btnStartSpin", startSpin);

    bindClick("btnDepositModal", () => {
        const m = document.getElementById("depositModal");
        if (m) m.classList.add("active");
    });
    bindClick("btnCloseDeposit", () => {
        const m = document.getElementById("depositModal");
        if (m) m.classList.remove("active");
    });

    bindClick("btnWithdrawModal", () => {
        if (!currentUser.trade_url) {
            alert("Skinlarni yechib olish uchun avval Profil bo'limida Steam Treyd-link havolangizni kiriting!");
            switchTab("profile");
        } else {
            fetch("/api/user/withdraw-request", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tg_id: currentUser.tg_id, trade_url: currentUser.trade_url })
            }).catch(e => console.error("withdraw req err:", e));

            alert(`Sizning Steam Treyd-linkingizga so'rov yuborildi!\nTez orada botimiz skinlarni yuboradi.`);
        }
    });

    bindClick("btnCloseTrade", () => {
        const m = document.getElementById("tradeModal");
        if (m) m.classList.remove("active");
    });
    bindClick("btnCloseBattle", () => {
        const m = document.getElementById("battleModal");
        if (m) m.classList.remove("active");
    });
    bindClick("btnCloseDouble", () => {
        const m = document.getElementById("doubleModal");
        if (m) m.classList.remove("active");
    });
    bindClick("btnCloseX50", () => {
        const m = document.getElementById("x50Modal");
        if (m) m.classList.remove("active");
    });

    bindClick("btnWinKeep", () => {
        const winM = document.getElementById("winModal");
        const caseM = document.getElementById("caseModal");
        if (winM) winM.classList.remove("active");
        if (caseM) caseM.classList.remove("active");
        renderInventory();
        renderProfileSkins();
    });

    bindClick("btnWinSell", async () => {
        if (userInventory.length > 0) {
            const lastItem = userInventory[0];
            try {
                const res = await fetch("/api/inventory/sell", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        tg_id: currentUser.tg_id,
                        item_id: lastItem.id
                    })
                });
                const data = await res.json();
                if (data.success) {
                    currentUser.balance = data.new_balance;
                    updateUI();
                    userInventory.shift();
                    renderInventory();
                    renderProfileSkins();
                }
            } catch (e) {
                console.error("Sell win skin error:", e);
            }
        }
        const winM = document.getElementById("winModal");
        const caseM = document.getElementById("caseModal");
        if (winM) winM.classList.remove("active");
        if (caseM) caseM.classList.remove("active");
    });

    bindClick("btnSellAll", async () => {
        if (userInventory.length === 0) return;
        try {
            const res = await fetch("/api/user/sell-all", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tg_id: currentUser.tg_id })
            });
            const data = await res.json();
            if (data.success) {
                currentUser.balance = data.new_balance;
                userInventory = [];
                updateUI();
                renderInventory();
                renderProfileSkins();
            }
        } catch (e) {
            console.error("Sell all error:", e);
        }
    });

    bindClick("btnPayConfirm", () => {
        let activeAmt = "4.0";
        const actEl = document.querySelector(".amt-btn.active");
        if (actEl) activeAmt = actEl.innerText.replace("$", "").trim();

        fetch("/api/user/deposit-request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id, amount: activeAmt, method: "Payme / Click / Humo" })
        }).catch(e => console.error("deposit req err:", e));

        alert("Payme / Click to'lov tizimi orqali balans to'ldirish arizangiz qabul qilindi!");
        currentUser.balance += parseFloat(activeAmt) || 4.0;
        updateUI();
        const m = document.getElementById("depositModal");
        if (m) m.classList.remove("active");
    });

    const amtBtns = document.querySelectorAll(".amt-btn");
    amtBtns.forEach(b => {
        b.onclick = () => {
            amtBtns.forEach(x => x.classList.remove("active"));
            b.classList.add("active");
        };
    });
}

// Boshlang'ich yuklash
function handleInitialUrlParams() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const targetTab = urlParams.get("tab");
        const openReward = urlParams.get("open_reward");

        if (targetTab === "profile" || openReward === "1") {
            switchTab("profile");

            setTimeout(() => {
                const box = document.getElementById("welcomeRewardBox");
                if (box) {
                    box.scrollIntoView({ behavior: "smooth", block: "center" });
                    box.classList.add("reward-highlight-pulse");
                    setTimeout(() => {
                        box.classList.remove("reward-highlight-pulse");
                    }, 5000);
                }
            }, 350);
        }
    } catch (e) {
        console.error("handleInitialUrlParams error:", e);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // 1. Birinchi navbatda barcha navigatsiya va tugmalarni ulaymiz (Darhol ishlashi uchun)
    setupNav();
    setupModals();
    setupGameCards();
    setupProfileSettings();
    renderCases();
    renderInventory();
    renderProfileSkins();
    renderLiveMarquee();
    if (typeof renderDoubleWheelSvg === "function") renderDoubleWheelSvg();
    if (typeof renderX50RingSvg === "function") renderX50RingSvg();
    handleInitialUrlParams();

    // 2. Serverdan ma'lumotlarni tortib olamiz
    let initData = tg?.initData || "";
    fetch(`/api/init?initData=${encodeURIComponent(initData)}`)
        .then(res => res.json())
        .then(data => {
            if (data) {
                if (data.user) {
                    currentUser = data.user;
                    setupWelcomeReward();
                }
                if (data.cases) allCases = data.cases;
                if (data.skins) allSkins = data.skins;
                if (data.inventory) userInventory = data.inventory;
                updateUI();
                renderCases();
                renderInventory();
                renderProfileSkins();
                renderLiveMarquee();
                handleInitialUrlParams();
            }
        })
        .catch(e => {
            console.log("Offline / default rejim:", e);
            updateUI();
            renderCases();
            renderLiveMarquee();
            handleInitialUrlParams();
        });
});
