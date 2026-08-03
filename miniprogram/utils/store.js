const { generateMockTripPlan } = require("./generate-mock-plan");

const STORAGE_KEY = "lvban-ai-trips";
const DEMO_TRIP_ID = "trip-dali-demo";

function toSummary(trip) {
  return {
    id: trip.id,
    title: trip.title,
    destination: trip.request.destination,
    startDate: trip.request.startDate,
    days: trip.request.days,
    travelers: trip.request.travelers,
    coverImage: trip.coverImage,
    status: trip.status,
    estimatedTotal: trip.budget.estimatedTotal,
  };
}

function createDemoTrip() {
  const trip = generateMockTripPlan({
    destination: "云南大理",
    startDate: "2026-08-15",
    endDate: "2026-08-17",
    days: 3,
    travelers: 2,
    budgetPerPerson: 2500,
    companionType: "couple",
    preferences: ["nature", "photo", "food", "relax"],
    intensity: "relaxed",
    selfDrive: false,
    specialRequests: "希望多拍洱海日出，少走回头路，晚上别排太满。",
    wakeUpTime: "08:00",
  });
  return Object.assign({}, trip, {
    id: DEMO_TRIP_ID,
    title: "大理风花雪月 · 3 日慢游",
    coverImage:
      "https://images.unsplash.com/photo-1547981609-4b6bfe67ca0b?auto=format&fit=crop&w=1600&q=80",
    status: "ready",
  });
}

function defaultState() {
  const demo = createDemoTrip();
  return {
    trips: [demo],
    summaries: [toSummary(demo)],
  };
}

function markReady(trip) {
  if (trip.status === "archived") return trip;
  if (trip.days && trip.days.length > 0) {
    return Object.assign({}, trip, { status: "ready" });
  }
  return trip;
}

function readState() {
  try {
    const raw = wx.getStorageSync(STORAGE_KEY);
    if (!raw || !Array.isArray(raw.trips) || raw.trips.length === 0) {
      const init = defaultState();
      writeState(init);
      return init;
    }
    const trips = raw.trips.map(markReady);
    const summaries = trips.map(toSummary);
    return { trips: trips, summaries: summaries };
  } catch (e) {
    const init = defaultState();
    writeState(init);
    return init;
  }
}

function writeState(state) {
  wx.setStorageSync(STORAGE_KEY, state);
}

function listSummaries() {
  return readState().summaries;
}

function getTrip(id) {
  return readState().trips.find(function (t) {
    return t.id === id;
  });
}

function createTrip(request) {
  const trip = Object.assign({}, generateMockTripPlan(request), { status: "ready" });
  const state = readState();
  const next = {
    trips: [trip].concat(state.trips.filter(function (t) { return t.id !== trip.id; })),
    summaries: [toSummary(trip)].concat(state.summaries.filter(function (s) { return s.id !== trip.id; })),
  };
  writeState(next);
  return trip;
}

function regenerateTrip(tripId) {
  const state = readState();
  const existing = state.trips.find(function (t) { return t.id === tripId; });
  if (!existing) return undefined;
  const regenerated = Object.assign({}, generateMockTripPlan(existing.request), {
    id: existing.id,
    createdAt: existing.createdAt,
    status: "ready",
  });
  writeState({
    trips: state.trips.map(function (t) { return t.id === tripId ? regenerated : t; }),
    summaries: state.summaries.map(function (s) {
      return s.id === tripId ? toSummary(regenerated) : s;
    }),
  });
  return regenerated;
}

function updateTripRequest(tripId, request) {
  const state = readState();
  const existing = state.trips.find(function (t) { return t.id === tripId; });
  if (!existing) return undefined;
  const now = new Date().toISOString();
  const regenerated = generateMockTripPlan(request);
  const updated = Object.assign({}, regenerated, {
    id: existing.id,
    createdAt: existing.createdAt,
    updatedAt: now,
    status: "ready",
    messages: existing.messages.concat([
      {
        id: "msg-adjust-" + Date.now(),
        role: "assistant",
        content:
          "已根据你调整后的需求，重新生成 " +
          request.destination +
          " " +
          request.days +
          " 日行程，状态为已完成。可继续在对话中微调细节。",
        createdAt: now,
      },
    ]),
  });
  writeState({
    trips: state.trips.map(function (t) { return t.id === tripId ? updated : t; }),
    summaries: state.summaries.map(function (s) {
      return s.id === tripId ? toSummary(updated) : s;
    }),
  });
  return updated;
}

function appendMessage(tripId, message) {
  const state = readState();
  writeState({
    trips: state.trips.map(function (trip) {
      if (trip.id !== tripId) return trip;
      return Object.assign({}, trip, {
        updatedAt: new Date().toISOString(),
        messages: trip.messages.concat([
          Object.assign({}, message, {
            id: "msg-" + Date.now(),
            createdAt: new Date().toISOString(),
          }),
        ]),
      });
    }),
    summaries: state.summaries,
  });
}

function toggleChecklistItem(tripId, itemId) {
  const state = readState();
  const trips = state.trips.map(function (trip) {
    if (trip.id !== tripId) return trip;
    return Object.assign({}, trip, {
      checklist: trip.checklist.map(function (item) {
        return item.id === itemId
          ? Object.assign({}, item, { checked: !item.checked })
          : item;
      }),
    });
  });
  writeState({ trips: trips, summaries: state.summaries });
  return trips.find(function (t) { return t.id === tripId; });
}

function mockAssistantReply(input) {
  if (input.indexOf("删除") >= 0 || input.indexOf("减少") >= 0) {
    return "好的，我只调整了相关节点：已移除对应景点，并重新串联前后交通时间，其余日期保持不变。";
  }
  if (input.indexOf("餐厅") >= 0 || input.indexOf("午餐") >= 0 || input.indexOf("便宜") >= 0) {
    return "已替换当日餐厅推荐，并同步更新餐饮预算。行程其他部分未改动。";
  }
  if (input.indexOf("预算") >= 0) {
    return "已下调住宿与购物占比，预计总费用下降约 15%，剩余预算已刷新。";
  }
  if (input.indexOf("下雨") >= 0) {
    return "已将指定日期切换为下雨备用方案，室内活动优先，户外观景已后移。";
  }
  if (input.indexOf("出发") >= 0 || input.indexOf("时间") >= 0) {
    return "已调整出发时间，并顺延当日后续节点，保证用餐与休息空隙。";
  }
  return "收到。我会只修改相关行程节点，不会重新生成整份计划。你可以继续提出更具体的调整。";
}

module.exports = {
  DEMO_TRIP_ID: DEMO_TRIP_ID,
  listSummaries: listSummaries,
  getTrip: getTrip,
  createTrip: createTrip,
  regenerateTrip: regenerateTrip,
  updateTripRequest: updateTripRequest,
  appendMessage: appendMessage,
  toggleChecklistItem: toggleChecklistItem,
  mockAssistantReply: mockAssistantReply,
};
