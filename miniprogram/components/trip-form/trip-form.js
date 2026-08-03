Component({
  properties: {
    value: {
      type: Object,
      value: {},
    },
  },
  data: {
    companionOptions: [
      { key: "solo", label: "独自出行" },
      { key: "couple", label: "情侣/夫妻" },
      { key: "family", label: "家庭亲子" },
      { key: "friends", label: "朋友结伴" },
      { key: "business", label: "商务出差" },
    ],
    intensityOptions: [
      { key: "relaxed", label: "悠闲慢游" },
      { key: "moderate", label: "适中节奏" },
      { key: "packed", label: "紧凑打卡" },
    ],
    preferenceOptions: [
      { key: "food", label: "美食探店" },
      { key: "nature", label: "自然风光" },
      { key: "culture", label: "文化体验" },
      { key: "photo", label: "摄影出片" },
      { key: "shopping", label: "逛街购物" },
      { key: "nightlife", label: "夜生活" },
      { key: "history", label: "历史古迹" },
      { key: "adventure", label: "户外冒险" },
      { key: "relax", label: "放松疗愈" },
    ],
    prefActive: {},
  },
  observers: {
    value: function (v) {
      const prefs = (v && v.preferences) || [];
      const prefActive = {};
      prefs.forEach(function (p) {
        prefActive[p] = true;
      });
      this.setData({ prefActive: prefActive });
    },
  },
  methods: {
    emit(patch) {
      const next = Object.assign({}, this.data.value || {}, patch);
      this.triggerEvent("change", { value: next });
    },
    onInput(e) {
      const field = e.currentTarget.dataset.field;
      const patch = {};
      patch[field] = e.detail.value;
      this.emit(patch);
    },
    onPicker(e) {
      const field = e.currentTarget.dataset.field;
      const patch = {};
      patch[field] = e.detail.value;
      this.emit(patch);
    },
    onNumber(e) {
      const field = e.currentTarget.dataset.field;
      const patch = {};
      patch[field] = Number(e.detail.value);
      this.emit(patch);
    },
    onCompanion(e) {
      this.emit({ companionType: e.currentTarget.dataset.key });
    },
    onIntensity(e) {
      this.emit({ intensity: e.currentTarget.dataset.key });
    },
    onPreference(e) {
      const key = e.currentTarget.dataset.key;
      const prefs = (this.data.value && this.data.value.preferences) || [];
      const next = prefs.indexOf(key) >= 0
        ? prefs.filter(function (p) { return p !== key; })
        : prefs.concat([key]);
      this.emit({ preferences: next });
    },
    onSelfDrive(e) {
      this.emit({ selfDrive: e.detail.value });
    },
  },
});
