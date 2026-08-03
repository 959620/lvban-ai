const { mealLabels, placeTypeLabels, transportLabels } = require("../../utils/labels");
Component({
  properties: {
    days: {
      type: Array,
      value: [],
    },
  },
  data: {
    activeDay: 1,
    current: null,
    placeTypeLabels,
    transportLabels,
    mealLabels,
  },
  observers: {
    days(days) {
      if (!days || !days.length) {
        this.setData({ current: null, activeDay: 1 });
        return;
      }
      const active = this.data.activeDay;
      const current = days.find((d) => d.day === active) || days[0];
      this.setData({ current, activeDay: current.day });
    },
  },
  methods: {
    onSelectDay(e) {
      const day = Number(e.currentTarget.dataset.day);
      const days = this.data.days;
      const current = days.find((d) => d.day === day) || days[0];
      this.setData({ activeDay: day, current });
    },
  },
});
