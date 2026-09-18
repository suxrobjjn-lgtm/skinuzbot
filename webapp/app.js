// SKENUZ Mini App Client Logic
const tg = window.Telegram ? window.Telegram.WebApp : null;

if (tg) {
    tg.ready();
    tg.expand();
}

// Global State
let currentUser = {
    tg_id: 123456789,
    first_name: "O'yinchi",
    username: "",
    balance: 10.00,
    trade_url: "",
    ref_count: 0
};

let allCases = [];
let allSkins = [];
let userInventory = [];
let currentCase = null;
let lastWonSkin = null;

// Haptic yordamchisi
function triggerHaptic(type = 'light') {
    if (tg && tg.HapticFeedback) {
        if (type === 'success') tg.HapticFeedback.notificationOccurred('success');
        else if (type === 'error') tg.HapticFeedback.notificationOccurred('error');
        else tg.HapticFeedback.impactOccurred(type);
    }
}

// 1. DASTURNI ISHGA TUSHIRISH
async function initApp() {
    let initData = "";
    if (tg && tg.initData) {
        initData = tg.initData;
    }

    try {
        const res = await fetch(`/api/init?initData=${encodeURIComponent(initData)}`);
        const data = await res.json();
        
        currentUser = data.user;
        allCases = data.cases;
        allSkins = data.skins;
        userInventory = data.inventory;

        updateUserUI();
        renderCases();
        renderLiveDrops(data.live_drops || []);
        renderInventory();
        setupUpgraderCatalog();
    } catch (e) {
        console.error("Init xatosi:", e);
        // Offline / Standalone demo ma'lumotlar
        currentUser.first_name = tg?.initDataUnsafe?.user?.first_name || "O'yinchi";
        updateUserUI();
    }

    setupTabs();
    setupModals();
    setupEvents();

    // Jonli yutuqlarni har 5 soniyada yangilab turish
    setInterval(fetchLiveDrops, 5000);
}

// 2. FOYDALANUVCHI INTERFEYSI
function updateUserUI() {
    document.getElementById("userName").innerText = currentUser.first_name || "O'yinchi";
    document.getElementById("userBalance").innerText = parseFloat(currentUser.balance).toFixed(2);
    document.getElementById("refCount").innerText = currentUser.ref_count || 0;
    document.getElementById("refLinkInput").value = `https://t.me/Skenuzbot?start=ref_${currentUser.tg_id}`;
    if (currentUser.trade_url) {
        document.getElementById("tradeUrlInput").value = currentUser.trade_url;
    }
}

// 3. TABLAR
function setupTabs() {
    const tabs = document.querySelectorAll(".nav-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            triggerHaptic('selection');
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            const target = tab.getAttribute("data-tab");
            document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
            const targetPane = document.getElementById(`pane-${target}`);
            if (targetPane) targetPane.classList.add("active");

            if (target === 'inventory') renderInventory();
            if (target === 'battles') renderBattles();
        });
    });
}

// 4. KEYSLAR VITRINASI
function renderCases() {
    const grid = document.getElementById("casesGrid");
    grid.innerHTML = "";

    allCases.forEach(c => {
        const card = document.createElement("div");
        card.className = "case-card";
        card.style.setProperty("--case-color", c.color);
        card.innerHTML = `
            <span class="case-badge">${c.badge}</span>
            <img class="case-image" src="${c.image}" alt="${c.name}" />
            <h4 class="case-name">${c.name}</h4>
            <div class="case-price-tag">${c.price > 0 ? c.price + '$' : 'BEPUL'}</div>
        `;
        card.addEventListener("click", () => openCasePreview(c));
        grid.appendChild(card);
    });
}

// 5. KEYSNI KO'RISH VA OCHISH MODALI
function openCasePreview(c) {
    triggerHaptic('light');
    currentCase = c;
    document.getElementById("modalCaseName").innerText = c.name;
    document.getElementById("modalCasePrice").innerText = c.price > 0 ? `${c.price}$` : "BEPUL";

    // Keys ichidagi skinlar ro'yxati
    const previewBox = document.getElementById("caseItemsPreview");
    previewBox.innerHTML = "";
    c.items.forEach(item => {
        const skin = allSkins.find(s => s.id === item.skin_id);
        if (!skin) return;
        const div = document.createElement("div");
        div.className = "preview-item";
        div.style.setProperty("--item-color", skin.color);
        div.innerHTML = `
            <img src="${skin.image}" alt="${skin.name}" />
            <span class="preview-item-name">${skin.name}</span>
            <span class="preview-item-price">${skin.price}$</span>
        `;
        previewBox.appendChild(div);
    });

    // Boshlang'ich lenta
    resetRouletteTrack(c);

    const btnOpen = document.getElementById("btnStartOpenCase");
    btnOpen.disabled = false;
    btnOpen.innerText = c.price > 0 ? `KEYSNI OCHISH (${c.price}$)` : "BEPUL OCHISH";

    document.getElementById("caseModal").classList.add("active");
}

function resetRouletteTrack(c) {
    const track = document.getElementById("rouletteTrack");
    track.style.transition = "none";
    track.style.transform = "translateX(0px)";
    track.innerHTML = "";

    // Boshlang'ich 15 ta ko'rinish
    for (let i = 0; i < 15; i++) {
        const randItem = c.items[Math.floor(Math.random() * c.items.length)];
        const skin = allSkins.find(s => s.id === randItem.skin_id);
        if (skin) {
            track.appendChild(createRouletteItem(skin));
        }
    }
}

function createRouletteItem(skin) {
    const div = document.createElement("div");
    div.className = "roulette-item";
    div.style.setProperty("--item-color", skin.color);
    div.innerHTML = `
        <img src="${skin.image}" alt="${skin.name}" />
        <span class="roulette-item-name">${skin.name}</span>
    `;
    return div;
}

// 6. ROULETTE AYLANTIRISH ANIMATSIYASI
async function startCaseOpening() {
    if (!currentCase) return;

    if (currentUser.balance < currentCase.price) {
        triggerHaptic('error');
        alert("Balansingizda mablag' yetarli emas! Iltimos, hisobingizni to'ldiring.");
        document.getElementById("depositModal").classList.add("active");
        return;
    }

    const btnOpen = document.getElementById("btnStartOpenCase");
    btnOpen.disabled = true;
    btnOpen.innerText = "Aylanmoqda...";
    triggerHaptic('heavy');

    // Serverga so'rov
    let wonSkin = null;
    try {
        const res = await fetch("/api/cases/open", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id, case_id: currentCase.id })
        });
        const data = await res.json();
        if (!data.success) {
            alert(data.error || "Xatolik yuz berdi");
            btnOpen.disabled = false;
            return;
        }
        wonSkin = data.won_skin;
        currentUser.balance = data.new_balance;
        userInventory.unshift(data.inventory_item);
        updateUserUI();
    } catch (e) {
        console.error("Open xatosi:", e);
        btnOpen.disabled = false;
        return;
    }

    lastWonSkin = wonSkin;

    // Lentani to'liq generatsiya qilish (55 ta element, 45-chisida g'olib skin)
    const track = document.getElementById("rouletteTrack");
    track.style.transition = "none";
    track.style.transform = "translateX(0px)";
    track.innerHTML = "";

    const totalCards = 55;
    const winIndex = 45;

    for (let i = 0; i < totalCards; i++) {
        if (i === winIndex) {
            track.appendChild(createRouletteItem(wonSkin));
        } else {
            const randItem = currentCase.items[Math.floor(Math.random() * currentCase.items.length)];
            const skin = allSkins.find(s => s.id === randItem.skin_id);
            track.appendChild(createRouletteItem(skin || wonSkin));
        }
    }

    // Har bir karta eni 100px.
    // Markaziy nishon: containerWidth / 2
    const containerWidth = document.querySelector(".roulette-container").offsetWidth;
    const cardWidth = 100;
    // Tasodifiy ozgina markazdan surilish (-25px dan +25px gacha)
    const randomOffset = Math.floor(Math.random() * 50) - 25;
    const targetTranslateX = (winIndex * cardWidth) + (cardWidth / 2) - (containerWidth / 2) + randomOffset;

    // Majburiy repaint
    track.offsetHeight;

    // CS2 aylanish animatsiyasi (5.5 soniya, cubic-bezier)
    track.style.transition = "transform 5.5s cubic-bezier(0.12, 0.8, 0.18, 1)";
    track.style.transform = `translateX(-${targetTranslateX}px)`;

    // Aylanish vaqtida tebranish (haptic ticker)
    let tickCount = 0;
    const tickInterval = setInterval(() => {
        tickCount++;
        if (tickCount % 4 === 0) triggerHaptic('light');
        if (tickCount > 25) clearInterval(tickInterval);
    }, 200);

    setTimeout(() => {
        clearInterval(tickInterval);
        triggerHaptic('success');
        showWinModal(wonSkin);
        btnOpen.disabled = false;
        btnOpen.innerText = "YANA OCHISH";
    }, 5600);
}

// 7. YUTUQ MODALI
function showWinModal(skin) {
    document.getElementById("winSkinImg").src = skin.image;
    document.getElementById("winSkinName").innerText = skin.name;
    document.getElementById("winSkinPrice").innerText = `${skin.price}$`;
    document.getElementById("winModal").classList.add("active");
}

// 8. INVENTAR
function renderInventory() {
    const grid = document.getElementById("inventoryGrid");
    grid.innerHTML = "";
    document.getElementById("invCount").innerText = userInventory.length;

    let totalVal = 0;
    userInventory.forEach(item => {
        totalVal += parseFloat(item.skin_price);
        const card = document.createElement("div");
        card.className = "inv-card";
        card.style.setProperty("--item-color", item.skin_color);
        card.innerHTML = `
            <img src="${item.skin_image}" alt="${item.skin_name}" />
            <span class="inv-name">${item.skin_name}</span>
            <span class="inv-price">${item.skin_price}$</span>
            <button class="btn-inv-sell" data-id="${item.id}">Sotish (${item.skin_price}$)</button>
        `;
        card.querySelector(".btn-inv-sell").addEventListener("click", () => sellItem(item.id));
        grid.appendChild(card);
    });

    document.getElementById("invTotalValue").innerText = `${totalVal.toFixed(2)}$`;
}

async function sellItem(itemId) {
    triggerHaptic('medium');
    try {
        const res = await fetch("/api/inventory/sell", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id, item_id: itemId })
        });
        const data = await res.json();
        if (data.success) {
            currentUser.balance = data.new_balance;
            userInventory = userInventory.filter(i => i.id !== itemId);
            updateUserUI();
            renderInventory();
            triggerHaptic('success');
        }
    } catch (e) {
        console.error("Sotish xatosi:", e);
    }
}

async function sellAllInventory() {
    if (userInventory.length === 0) return;
    triggerHaptic('heavy');
    try {
        const res = await fetch("/api/inventory/sell-all", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id })
        });
        const data = await res.json();
        if (data.success) {
            currentUser.balance = data.new_balance;
            userInventory = [];
            updateUserUI();
            renderInventory();
            alert(`Jami ${data.total_sold}$ balansga qo'shildi!`);
        }
    } catch (e) {
        console.error("Barchasini sotish xatosi:", e);
    }
}

// 9. JONLI DROPLAR (LIVE TICKER)
async function fetchLiveDrops() {
    try {
        const res = await fetch("/api/live-drops");
        const data = await res.json();
        renderLiveDrops(data);
    } catch (e) {}
}

function renderLiveDrops(drops) {
    const track = document.getElementById("liveTrack");
    track.innerHTML = "";
    drops.forEach(d => {
        const el = document.createElement("div");
        el.className = "live-item";
        el.style.setProperty("--item-color", d.skin_color);
        el.innerHTML = `
            <img src="${d.skin_image}" alt="${d.skin_name}" />
            <div class="live-item-meta">
                <span class="live-item-name">${d.skin_name}</span>
                <span class="live-item-price">${d.skin_price}$</span>
            </div>
        `;
        track.appendChild(el);
    });
}

// 10. UPGRADER LOGIKASI
let selectedUpgradeSource = null;
let selectedUpgradeTarget = null;

function setupUpgraderCatalog() {
    const list = document.getElementById("targetSkinsList");
    list.innerHTML = "";
    
    allSkins.filter(s => s.price > 15).forEach(skin => {
        const div = document.createElement("div");
        div.className = "preview-item";
        div.style.cursor = "pointer";
        div.style.setProperty("--item-color", skin.color);
        div.innerHTML = `
            <img src="${skin.image}" alt="${skin.name}" />
            <span class="preview-item-name">${skin.name}</span>
            <span class="preview-item-price">${skin.price}$</span>
        `;
        div.addEventListener("click", () => selectUpgradeTarget(skin));
        list.appendChild(div);
    });

    document.getElementById("upgradeSourceBox").addEventListener("click", selectUpgradeSource);
    document.getElementById("btnRollUpgrade").addEventListener("click", executeUpgrade);
}

function selectUpgradeSource() {
    if (userInventory.length === 0) {
        alert("Inventaringizda skin yo'q! Avval biror keys oching.");
        return;
    }
    // Avtomatik birinchi skinni olamiz
    selectedUpgradeSource = userInventory[0];
    const box = document.getElementById("upgradeSourceBox");
    box.classList.add("has-item");
    box.innerHTML = `
        <img src="${selectedUpgradeSource.skin_image}" />
        <span style="font-size:10px;">${selectedUpgradeSource.skin_name}</span>
        <strong style="color:var(--accent-gold); font-size:10px;">${selectedUpgradeSource.skin_price}$</strong>
    `;
    recalcUpgradeChance();
}

function selectUpgradeTarget(skin) {
    selectedUpgradeTarget = skin;
    const box = document.getElementById("upgradeTargetBox");
    box.classList.add("has-item");
    box.innerHTML = `
        <img src="${skin.image}" />
        <span style="font-size:10px;">${skin.name}</span>
        <strong style="color:var(--accent-gold); font-size:10px;">${skin.price}$</strong>
    `;
    recalcUpgradeChance();
}

function recalcUpgradeChance() {
    if (!selectedUpgradeSource || !selectedUpgradeTarget) return;

    let chance = (selectedUpgradeSource.skin_price / selectedUpgradeTarget.price) * 90; // 90% RTP
    if (chance > 80) chance = 80;
    if (chance < 1) chance = 1;

    document.getElementById("upgradeChanceVal").innerText = `${chance.toFixed(1)}%`;
    document.getElementById("btnRollUpgrade").disabled = false;
}

async function executeUpgrade() {
    if (!selectedUpgradeSource || !selectedUpgradeTarget) return;

    const btn = document.getElementById("btnRollUpgrade");
    btn.disabled = true;
    triggerHaptic('heavy');

    const wheel = document.getElementById("upgradeWheel");
    const randomRot = 1440 + Math.floor(Math.random() * 360);
    wheel.style.transition = "transform 4s cubic-bezier(0.1, 0.8, 0.2, 1)";
    wheel.style.transform = `rotate(${randomRot}deg)`;

    try {
        const res = await fetch("/api/upgrader/roll", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                tg_id: currentUser.tg_id,
                source_item_id: selectedUpgradeSource.id,
                target_skin_id: selectedUpgradeTarget.id
            })
        });
        const data = await res.json();

        setTimeout(() => {
            if (data.is_win) {
                triggerHaptic('success');
                alert(`🎉 G'ALABA! Siz ${selectedUpgradeTarget.name} yutib oldingiz!`);
                userInventory.unshift(data.won_item);
            } else {
                triggerHaptic('error');
                alert("😔 Afsuski bu safar omad kelmadi. Skiningiz yutqazildi.");
            }
            userInventory = userInventory.filter(i => i.id !== selectedUpgradeSource.id);
            selectedUpgradeSource = null;
            document.getElementById("upgradeSourceBox").classList.remove("has-item");
            document.getElementById("upgradeSourceBox").innerHTML = `<span class="placeholder">+ Inventardan tanlang</span>`;
            document.getElementById("upgradeChanceVal").innerText = "0%";
            wheel.style.transition = "none";
            wheel.style.transform = "rotate(0deg)";
            btn.disabled = true;
            renderInventory();
        }, 4200);

    } catch (e) {
        btn.disabled = false;
    }
}

// 11. CASE BATTLES (JANG)
function renderBattles() {
    const list = document.getElementById("battlesList");
    list.innerHTML = `
        <div class="bonus-card" style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <strong>⚔️ BOT vs O'YINCHI (Starter Case)</strong>
                <p style="font-size:11px; margin:2px 0;">Stavka: 1.99$ | G'olib barcha skinlarni oladi!</p>
            </div>
            <button class="btn-preset active" id="btnBattleBot" style="flex:none; padding:8px 16px;">Jangga Kirish</button>
        </div>
    `;

    document.getElementById("btnBattleBot")?.addEventListener("click", async () => {
        if (currentUser.balance < 1.99) {
            alert("Jang uchun balansingizda 1.99$ yetarli emas!");
            return;
        }
        triggerHaptic('heavy');
        alert("⚔️ Bot bilan jang boshlandi! Ikkala taraf keys ochmoqda...");
        try {
            const res = await fetch("/api/battle/bot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tg_id: currentUser.tg_id, case_id: "starter" })
            });
            const data = await res.json();
            currentUser.balance = data.new_balance;
            updateUserUI();

            if (data.is_win) {
                triggerHaptic('success');
                alert(`🏆 SIZ G'ALABA QOZONDINGIZ!\nSizning skiningiz: ${data.user_skin.name} (${data.user_skin.price}$)\nBotning skiningiz: ${data.bot_skin.name} (${data.bot_skin.price}$)\nIkkala skin ham inventaringizga qo'shildi!`);
                userInventory.unshift(data.user_item, data.bot_item);
            } else {
                triggerHaptic('error');
                alert(`😔 Bot g'olib bo'ldi!\nSiz: ${data.user_skin.name} (${data.user_skin.price}$)\nBot: ${data.bot_skin.name} (${data.bot_skin.price}$)`);
            }
            renderInventory();
        } catch (e) {
            console.error(e);
        }
    });
}

// 12. MODALLAR VA EVENTLAR
function setupModals() {
    document.getElementById("btnCloseCaseModal").addEventListener("click", () => {
        document.getElementById("caseModal").classList.remove("active");
    });

    document.getElementById("btnStartOpenCase").addEventListener("click", startCaseOpening);

    document.getElementById("btnDepositModal").addEventListener("click", () => {
        document.getElementById("depositModal").classList.add("active");
    });
    document.getElementById("btnCloseDeposit").addEventListener("click", () => {
        document.getElementById("depositModal").classList.remove("active");
    });

    document.getElementById("btnWinKeep").addEventListener("click", () => {
        document.getElementById("winModal").classList.remove("active");
        document.getElementById("caseModal").classList.remove("active");
    });

    document.getElementById("btnWinSell").addEventListener("click", async () => {
        if (userInventory.length > 0) {
            await sellItem(userInventory[0].id);
        }
        document.getElementById("winModal").classList.remove("active");
        document.getElementById("caseModal").classList.remove("active");
    });

    document.getElementById("btnSellAll").addEventListener("click", sellAllInventory);
}

function setupEvents() {
    // Kunlik bonus olish
    document.getElementById("btnClaimDaily").addEventListener("click", async () => {
        triggerHaptic('medium');
        try {
            const res = await fetch("/api/daily", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tg_id: currentUser.tg_id })
            });
            const data = await res.json();
            if (data.success) {
                currentUser.balance = data.new_balance;
                updateUserUI();
                triggerHaptic('success');
                alert("🎉 Kunlik 1.00$ bonus hisobingizga qo'shildi!");
            } else {
                alert(`⚠️ Bonus har 24 soatda beriladi. Qolgan vaqt: ${Math.ceil(data.remaining / 3600)} soat.`);
            }
        } catch (e) {}
    });

    // Trade URL saqlash
    document.getElementById("btnSaveTradeUrl").addEventListener("click", async () => {
        const val = document.getElementById("tradeUrlInput").value;
        if (!val.includes("steamcommunity.com")) {
            alert("Iltimos, haqiqiy Steam Trade URL havolasini kiriting!");
            return;
        }
        triggerHaptic('success');
        await fetch("/api/trade-url", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id, trade_url: val })
        });
        alert("✅ Steam Trade URL muvaffaqiyatli saqlangandi!");
    });

    // Referal nusxalash
    document.getElementById("btnCopyRef").addEventListener("click", () => {
        const refInp = document.getElementById("refLinkInput");
        refInp.select();
        document.execCommand("copy");
        triggerHaptic('success');
        alert("Referal havolangiz nusxalandi! Do'stlaringizga yuboring va har biriga 2.00$ oling.");
    });

    // Promokod faollashtirish
    document.getElementById("btnApplyPromo").addEventListener("click", async () => {
        const val = document.getElementById("promoInput").value.trim().toUpperCase();
        if (!val) return;
        triggerHaptic('medium');
        try {
            const res = await fetch("/api/promo", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tg_id: currentUser.tg_id, code: val })
            });
            const data = await res.json();
            if (data.success) {
                currentUser.balance = data.new_balance;
                updateUserUI();
                triggerHaptic('success');
                alert(`🎉 Promokod faollashtirildi! Balansingizga ${data.amount}$ qo'shildi!`);
            } else {
                alert(data.error || "Bunday promokod mavjud emas yoki tugagan.");
            }
        } catch (e) {}
    });

    // To'lovni tasdiqlash
    document.getElementById("btnConfirmDeposit").addEventListener("click", () => {
        const amt = document.getElementById("depositCustomAmt").value;
        triggerHaptic('success');
        alert(`To'lov tizimi (Payme/Click) yuklanmoqda... Summa: ${amt}$`);
        // Test rejimida avtomatik hisobga qo'shish imkoniyati:
        fetch("/api/deposit/test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tg_id: currentUser.tg_id, amount: parseFloat(amt) })
        }).then(r => r.json()).then(data => {
            currentUser.balance = data.new_balance;
            updateUserUI();
            document.getElementById("depositModal").classList.remove("active");
            alert(`✅ ${amt}$ hisobingizga muvaffaqiyatli to'ldirildi!`);
        });
    });
}

// Boshlash
window.addEventListener("DOMContentLoaded", initApp);
