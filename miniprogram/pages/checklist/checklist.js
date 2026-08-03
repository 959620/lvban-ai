const { getTrip, toggleChecklistItem } = require("../../utils/store");

Page({
  data: {
    tripId: "",
    missing: false,
    groups: [],
    done: 0,
    total: 0,
    percent: 0,
  },
  onLoad(query) {
    const tripId = query.id || "";
    this.setData({ tripId: tripId });
    this.load(tripId);
  },
  onShow() {
    if (this.data.tripId) this.load(this.data.tripId);
  },
  load(tripId) {
    const trip = getTrip(tripId);
    if (!trip) {
      this.setData({ missing: true });
      return;
    }
    const map = {};
    trip.checklist.forEach(function (item) {
      map[item.category] = map[item.category] || [];
      map[item.category].push(item);
    });
    const groups = Object.keys(map).map(function (category) {
      return { category: category, items: map[category] };
    });
    const done = trip.checklist.filter(function (i) { return i.checked; }).length;
    const total = trip.checklist.length;
    this.setData({
      missing: false,
      groups: groups,
      done: done,
      total: total,
      percent: total ? Math.round((done / total) * 100) : 0,
    });
  },
  onToggle(e) {
    const id = e.currentTarget.dataset.id;
    toggleChecklistItem(this.data.tripId, id);
    this.load(this.data.tripId);
  },
  goDetail() {
    const id = this.data.tripId;
    wx.navigateBack({
      fail: function () {
        wx.redirectTo({ url: "/pages/detail/detail?id=" + id });
      },
    });
  },
});
