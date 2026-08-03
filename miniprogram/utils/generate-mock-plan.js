const { sumBudget } = require("./labels");

const AREA_THEMES = [
  { area: "市中心核心区", title: "初到安顿", theme: "熟悉主城区与交通" },
  { area: "自然风光带", title: "山水一日", theme: "集中游览自然景观" },
  { area: "文化街区", title: "人文漫步", theme: "博物馆与老街体验" },
  { area: "美食购物区", title: "味道与市集", theme: "本地餐饮与伴手礼" },
  { area: "近郊轻松线", title: "近郊慢游", theme: "低强度观景与休息" },
  { area: "夜景休闲区", title: "夜色收尾", theme: "夜景、咖啡与轻松散步" },
];

const GENERIC_SPOTS = [
  {
    name: "地标观景台",
    type: "viewpoint",
    area: "市中心核心区",
    duration: "1 小时",
    cost: 60,
    reason: "快速建立对目的地的空间印象，适合拍照打卡。",
    notes: "高峰时段人多，可错峰到达。",
    prefs: ["photo", "culture"],
  },
  {
    name: "城市中央公园",
    type: "park",
    area: "市中心核心区",
    duration: "1.5 小时",
    cost: 0,
    reason: "步行友好，适合调节节奏和休息。",
    notes: "带水和防晒霜。",
    prefs: ["nature", "relax", "photo"],
  },
  {
    name: "老街步行区",
    type: "attraction",
    area: "文化街区",
    duration: "2 小时",
    cost: 0,
    reason: "本地生活气息浓，适合慢慢逛。",
    notes: "石板路注意防滑。",
    prefs: ["culture", "history", "shopping", "food"],
  },
  {
    name: "地方历史博物馆",
    type: "museum",
    area: "文化街区",
    duration: "1.5 小时",
    cost: 40,
    reason: "帮助理解当地文化背景，雨天也友好。",
    notes: "周一可能闭馆，出发前确认。",
    prefs: ["culture", "history"],
  },
  {
    name: "湖畔 / 海岸步道",
    type: "park",
    area: "自然风光带",
    duration: "2 小时",
    cost: 0,
    reason: "开阔视野，适合放松与摄影。",
    notes: "午后紫外线强，做好防晒。",
    prefs: ["nature", "photo", "relax"],
  },
  {
    name: "近郊观景点",
    type: "viewpoint",
    area: "近郊轻松线",
    duration: "2 小时",
    cost: 80,
    reason: "与市区景点分区安排，减少来回折返。",
    notes: "预留返程交通时间。",
    prefs: ["nature", "adventure", "photo"],
  },
  {
    name: "轻徒步步道",
    type: "park",
    area: "自然风光带",
    duration: "2.5 小时",
    cost: 30,
    reason: "满足户外偏好，同时控制强度。",
    notes: "穿防滑鞋，量力而行。",
    prefs: ["adventure", "nature"],
  },
  {
    name: "本地市集",
    type: "shopping",
    area: "美食购物区",
    duration: "1.5 小时",
    cost: 120,
    reason: "适合买伴手礼和试吃小吃。",
    notes: "保管好随身物品。",
    prefs: ["shopping", "food"],
  },
  {
    name: "夜景步道",
    type: "viewpoint",
    area: "夜景休闲区",
    duration: "1 小时",
    cost: 0,
    reason: "白天行程后轻松收尾，适合出片。",
    notes: "夜间注意保暖和交通安全。",
    prefs: ["nightlife", "photo", "relax"],
  },
  {
    name: "手作 / 文创街区",
    type: "shopping",
    area: "文化街区",
    duration: "1.5 小时",
    cost: 80,
    reason: "室内外结合，可灵活应对天气。",
    notes: "可控制消费预算。",
    prefs: ["shopping", "culture", "photo"],
  },
];

function addDays(dateStr, offset) {
  const date = new Date(`${dateStr}T12:00:00`);
  date.setDate(date.getDate() + offset);
  return date.toISOString().slice(0, 10);
}

function wakeHour(request) {
  const raw = request.wakeUpTime || "08:00";
  const hour = Number(raw.split(":")[0]);
  return Number.isFinite(hour) ? hour : 8;
}

function formatTime(hour, minute = 0) {
  return `${String(hour).padStart(2, "0")}:${String(minute).padStart(2, "0")}`;
}

function spotsPerDay(intensity) {
  if (intensity === "relaxed") return 3;
  if (intensity === "packed") return 5;
  return 4;
}

function transportFor(request, sameArea) {
  if (sameArea) return { mode: "walk", duration: "10 分钟", cost: 0 };
  if (request.selfDrive) return { mode: "drive", duration: "25 分钟", cost: 40 };
  return { mode: "taxi", duration: "20 分钟", cost: 35 };
}

function pickSpots(request, dayIndex, count) {
  const theme = AREA_THEMES[dayIndex % AREA_THEMES.length];
  const ranked = [...GENERIC_SPOTS].sort((a, b) => {
    const score = (spot) => {
      const prefScore = spot.prefs.filter((p) => request.preferences.includes(p)).length;
      const areaScore = spot.area === theme.area ? 2 : 0;
      return prefScore * 3 + areaScore;
    };
    return score(b) - score(a);
  });

  const selected = [];
  for (const spot of ranked) {
    if (selected.length >= count) break;
    if (selected.some((s) => s.name === spot.name)) continue;
    selected.push({
      ...spot,
      name: `${request.destination}·${spot.name}`,
      area: theme.area,
    });
  }

  while (selected.length < count) {
    const fallback = GENERIC_SPOTS[selected.length % GENERIC_SPOTS.length];
    selected.push({
      ...fallback,
      name: `${request.destination}·${fallback.name} ${selected.length + 1}`,
      area: theme.area,
    });
  }

  return { theme, spots: selected };
}

function buildFoods(
  destination,
  area,
  nearPlace,
  budgetLevel
) {
  const factor = budgetLevel === "low" ? 0.7 : budgetLevel === "high" ? 1.3 : 1;
  return [
    {
      id: `${area}-bf`,
      mealType: "breakfast",
      name: `${destination}本地早餐铺`,
      cuisine: "地方早餐",
      reason: "出行前快速补给，靠近当日活动区域。",
      estimatedCost: Math.round(35 * factor),
      walkingMinutes: 6,
      nearPlace,
    },
    {
      id: `${area}-lunch`,
      mealType: "lunch",
      name: `${area}人气午餐店`,
      cuisine: "本地家常",
      reason: "与上午景点同区，避免跨城吃饭。",
      estimatedCost: Math.round(75 * factor),
      walkingMinutes: 8,
      nearPlace,
    },
    {
      id: `${area}-cafe`,
      mealType: "cafe",
      name: `${area}休息咖啡馆`,
      cuisine: "咖啡轻食",
      reason: "下午行程间补水歇脚。",
      estimatedCost: Math.round(42 * factor),
      walkingMinutes: 5,
      nearPlace,
    },
    {
      id: `${area}-dinner`,
      mealType: "dinner",
      name: `${destination}特色晚餐`,
      cuisine: "地方特色",
      reason: "按你的偏好安排口味，控制步行距离。",
      estimatedCost: Math.round(110 * factor),
      walkingMinutes: 10,
      nearPlace: area,
    },
  ];
}

function buildDayNodes(
  request,
  day,
  spots,
  area
) {
  const start = wakeHour(request) + (day === 1 ? 1 : 0);
  const nodes = [];
  let hour = start;
  let prevArea = area;

  spots.forEach((spot, index) => {
    const sameArea = spot.area === prevArea || index === 0;
    const transport = transportFor(request, sameArea);
    const mealGap = index === 1 ? 1 : 0;
    hour += mealGap;

    nodes.push({
      id: `d${day}-n${index + 1}`,
      time: formatTime(Math.min(hour, 20), index % 2 === 0 ? 0 : 30),
      placeName: spot.name,
      placeType: spot.type,
      reason: spot.reason,
      suggestedDuration: spot.duration,
      transport: transport.mode,
      transportDuration: transport.duration,
      estimatedCost: spot.cost + transport.cost,
      notes: request.specialRequests
        ? `${spot.notes}（已考虑：${request.specialRequests}）`
        : spot.notes,
      area: spot.area,
    });

    hour += request.intensity === "packed" ? 1 : 2;
    prevArea = spot.area;
  });

  nodes.push({
    id: `d${day}-dinner`,
    time: formatTime(Math.min(hour + 1, 19), 30),
    placeName: `${request.destination}·${area}晚餐`,
    placeType: "restaurant",
    reason: "就近用餐，避免跨区奔波。",
    suggestedDuration: "1 小时",
    transport: "walk",
    transportDuration: "8 分钟",
    estimatedCost: Math.round(request.budgetPerPerson * 0.04),
    notes: "量力点菜，为次日行程保留体力。",
    area,
  });

  return nodes;
}

function buildDayPlan(request, dayIndex) {
  const day = dayIndex + 1;
  const count = spotsPerDay(request.intensity);
  const { theme, spots } = pickSpots(request, dayIndex, count);
  const budgetLevel =
    request.budgetPerPerson < 1500 ? "low" : request.budgetPerPerson > 3500 ? "high" : "mid";
  const nodes = buildDayNodes(request, day, spots, theme.area);
  const near = spots[0]?.name ?? theme.area;

  return {
    day,
    date: addDays(request.startDate, dayIndex),
    title: theme.title,
    theme: theme.theme,
    area: theme.area,
    summary: `第 ${day} 天集中安排「${theme.area}」，减少跨区折返；节奏按「${
      request.intensity === "relaxed" ? "悠闲" : request.intensity === "packed" ? "紧凑" : "适中"
    }」控制。`,
    nodes,
    foods: buildFoods(request.destination, theme.area, near, budgetLevel),
    backups: [
      {
        scenario: "rain",
        title: "下雨备用：室内优先",
        summary: "改为博物馆 / 咖啡馆 / 市集室内区域。",
        nodes: [
          {
            id: `d${day}-rain`,
            time: "10:30",
            placeName: `${request.destination}室内文化馆`,
            placeType: "museum",
            reason: "避开雨势，保留当日主题体验。",
            suggestedDuration: "2 小时",
            transport: request.selfDrive ? "drive" : "taxi",
            transportDuration: "20 分钟",
            estimatedCost: 40,
            notes: "出发前确认开放时间。",
            area: theme.area,
          },
        ],
      },
      {
        scenario: "tired",
        title: "太累备用：减量休息",
        summary: "去掉最远景点，增加咖啡休息时间。",
        nodes: [
          {
            id: `d${day}-tired`,
            time: "15:00",
            placeName: `${theme.area}休息咖啡馆`,
            placeType: "cafe",
            reason: "降低步行强度，保留核心体验。",
            suggestedDuration: "1.5 小时",
            transport: "walk",
            transportDuration: "5 分钟",
            estimatedCost: 50,
            notes: "可提前结束返回住宿。",
            area: theme.area,
          },
        ],
      },
      {
        scenario: "closed",
        title: "景点关闭备用：同区替换",
        summary: "用同区域备选点替换，不跨城重排。",
        nodes: [
          {
            id: `d${day}-closed`,
            time: "11:00",
            placeName: `${theme.area}备选步行街`,
            placeType: "attraction",
            reason: "同区替换，交通成本最低。",
            suggestedDuration: "1.5 小时",
            transport: "walk",
            transportDuration: "12 分钟",
            estimatedCost: 0,
            notes: "可顺便解决午餐。",
            area: theme.area,
          },
        ],
      },
    ],
  };
}

function buildBudget(request) {
  const totalBudget = request.budgetPerPerson * request.travelers;
  const days = request.days;
  const lodgingPerNight = Math.round(request.budgetPerPerson * 0.28);
  const breakdown = {
    lodging: lodgingPerNight * Math.max(days - 1, 1) * (request.travelers > 2 ? 2 : 1),
    transport: Math.round(totalBudget * 0.14),
    food: Math.round(request.budgetPerPerson * 0.18 * days * request.travelers),
    tickets: Math.round(request.budgetPerPerson * 0.08 * days * request.travelers),
    shopping: Math.round(totalBudget * 0.08),
    other: Math.round(totalBudget * 0.04),
  };

  const raw = sumBudget(breakdown);
  const target = Math.round(totalBudget * 0.86);
  const scale = raw === 0 ? 1 : target / raw;
  const scaled = {
    lodging: Math.round(breakdown.lodging * scale),
    transport: Math.round(breakdown.transport * scale),
    food: Math.round(breakdown.food * scale),
    tickets: Math.round(breakdown.tickets * scale),
    shopping: Math.round(breakdown.shopping * scale),
    other: Math.round(breakdown.other * scale),
  };
  const estimatedTotal = sumBudget(scaled);

  return {
    totalBudget,
    estimatedTotal,
    remaining: totalBudget - estimatedTotal,
    breakdown: scaled,
    currency: "CNY",
  };
}

function buildChecklist(request) {
  const items = [
    { id: "ck-1", category: "证件", label: "身份证 / 护照", checked: false, essential: true },
    { id: "ck-2", category: "证件", label: "酒店与行程确认截图", checked: false, essential: true },
    { id: "ck-3", category: "穿着", label: "舒适步行鞋", checked: false, essential: true },
    { id: "ck-4", category: "健康", label: "防晒霜与常用药", checked: false, essential: true },
    { id: "ck-5", category: "数码", label: "充电宝与数据线", checked: false, essential: true },
    { id: "ck-6", category: "出行", label: "折叠伞 / 薄外套", checked: false, essential: true },
  ];

  if (request.selfDrive) {
    items.push({
      id: "ck-7",
      category: "出行",
      label: "驾驶证与车辆检查",
      checked: false,
      essential: true,
    });
  }
  if (request.preferences.includes("photo")) {
    items.push({
      id: "ck-8",
      category: "数码",
      label: "相机 / 备用存储卡",
      checked: false,
      essential: false,
    });
  }
  if (request.preferences.includes("adventure")) {
    items.push({
      id: "ck-9",
      category: "穿着",
      label: "户外防滑鞋与速干衣",
      checked: false,
      essential: true,
    });
  }

  return items;
}

const COVER_BY_PREF = {
  nature:
    "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=1600&q=80",
  food: "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=1600&q=80",
  culture:
    "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1600&q=80",
  photo:
    "https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?auto=format&fit=crop&w=1600&q=80",
  shopping:
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1600&q=80",
  nightlife:
    "https://images.unsplash.com/photo-1514565131-fce0801e5785?auto=format&fit=crop&w=1600&q=80",
  history:
    "https://images.unsplash.com/photo-1552832230-c0197dd311b5?auto=format&fit=crop&w=1600&q=80",
  adventure:
    "https://images.unsplash.com/photo-1551632811-561732d1e306?auto=format&fit=crop&w=1600&q=80",
  relax:
    "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
};
function generateMockTripPlan(request) {
  const days = Math.min(Math.max(request.days, 1), 14);
  const normalized = { ...request, days };
  const dayPlans = Array.from({ length: days }, (_, i) => buildDayPlan(normalized, i));
  const budget = buildBudget(normalized);
  const mainPref = normalized.preferences[0] ?? "photo";
  const intensityLabel =
    normalized.intensity === "relaxed"
      ? "悠闲"
      : normalized.intensity === "packed"
        ? "紧凑"
        : "适中";

  return {
    id: `trip-${Date.now()}`,
    title: `${normalized.destination} · ${days} 日行程`,
    coverImage: COVER_BY_PREF[mainPref],
    status: "ready",
    request: normalized,
    days: dayPlans,
    budget,
    checklist: buildChecklist(normalized),
    messages: [
      {
        id: "boot-1",
        role: "assistant",
        content: `已根据你的偏好生成 ${normalized.destination} ${days} 日详细行程（${intensityLabel}节奏）。每天按区域集中安排，并附带美食与备用方案。可直接让我删景点、换餐厅或降低预算。`,
        createdAt: new Date().toISOString(),
      },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
}

module.exports = { generateMockTripPlan };
