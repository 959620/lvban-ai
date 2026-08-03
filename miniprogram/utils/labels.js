function formatCurrency(amount) {
  const n = Math.round(Number(amount) || 0);
  return `¥${n.toLocaleString("zh-CN")}`;
}

function sumBudget(breakdown) {
  return (
    breakdown.lodging +
    breakdown.transport +
    breakdown.food +
    breakdown.tickets +
    breakdown.shopping +
    breakdown.other
  );
}

const companionLabels = {
  solo: "独自出行",
  couple: "情侣/夫妻",
  family: "家庭亲子",
  friends: "朋友结伴",
  business: "商务出差",
};

const intensityLabels = {
  relaxed: "悠闲慢游",
  moderate: "适中节奏",
  packed: "紧凑打卡",
};

const preferenceLabels = {
  food: "美食探店",
  nature: "自然风光",
  culture: "文化体验",
  photo: "摄影出片",
  shopping: "逛街购物",
  nightlife: "夜生活",
  history: "历史古迹",
  adventure: "户外冒险",
  relax: "放松疗愈",
};

const placeTypeLabels = {
  attraction: "景点",
  restaurant: "餐厅",
  cafe: "咖啡",
  hotel: "住宿",
  transport: "交通",
  shopping: "购物",
  rest: "休息",
  viewpoint: "观景点",
  museum: "博物馆",
  park: "公园",
};

const transportLabels = {
  walk: "步行",
  metro: "地铁",
  bus: "公交",
  taxi: "打车",
  drive: "自驾",
  bike: "骑行",
  ferry: "轮渡",
  none: "无需交通",
};

const budgetCategoryLabels = {
  lodging: "住宿",
  transport: "交通",
  food: "餐饮",
  tickets: "门票",
  shopping: "购物",
  other: "其他",
};

const statusLabels = {
  draft: "草稿",
  planning: "规划中",
  ready: "已完成",
  archived: "已归档",
};

const mealLabels = {
  breakfast: "早餐",
  lunch: "午餐",
  dinner: "晚餐",
  cafe: "咖啡",
};

module.exports = {
  formatCurrency,
  sumBudget,
  companionLabels,
  intensityLabels,
  preferenceLabels,
  placeTypeLabels,
  transportLabels,
  budgetCategoryLabels,
  statusLabels,
  mealLabels,
};
