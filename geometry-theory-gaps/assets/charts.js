// assets/charts.js
// 共扼谱几何论缺口分析报告 - 图表

(function() {
  var style = getComputedStyle(document.documentElement);
  var accent = style.getPropertyValue('--accent').trim();
  var accent2 = style.getPropertyValue('--accent2').trim();
  var ink = style.getPropertyValue('--ink').trim();
  var muted = style.getPropertyValue('--muted').trim();
  var rule = style.getPropertyValue('--rule').trim();
  var bg2 = style.getPropertyValue('--bg2').trim();
  var crit = style.getPropertyValue('--crit').trim();
  var high = style.getPropertyValue('--high').trim();
  var med = style.getPropertyValue('--med').trim();
  var low = style.getPropertyValue('--low').trim();
  var bg = style.getPropertyValue('--bg').trim();

  // --- Chart 1: 各卷文件大小分布 ---
  var chart1 = echarts.init(document.getElementById('chart-volume-size'), null, { renderer: 'svg' });

  var volumes = ['卷0', '卷1', '卷2', '卷3', '卷4', '卷5', '卷6', '卷7', '卷8', '卷9', '卷10'];
  var maxSizes = [45061, 27836, 45766, 62471, 14955, 15399, 26400, 53109, 50311, 72186, 67538];
  var minSizes = [17304, 20113, 14592, 12980, 10558, 10940, 16800, 15474, 14420, 15405, 12784];
  var avgSizes = [26564, 23456, 26000, 29634, 13300, 13100, 20800, 31200, 28400, 34000, 30000];

  chart1.setOption({
    animation: false,
    tooltip: {
      trigger: 'axis',
      appendToBody: true,
      formatter: function(params) {
        var v = params[0].axisValue;
        var txt = '<strong>' + v + '</strong><br/>';
        params.forEach(function(p) {
          txt += p.marker + ' ' + p.seriesName + ': ' + (p.value / 1000).toFixed(1) + ' KB<br/>';
        });
        return txt;
      }
    },
    legend: {
      data: ['最大文件', '平均大小', '最小文件'],
      bottom: 0,
      textStyle: { color: muted, fontSize: 12 },
      icon: 'roundRect'
    },
    grid: { left: 50, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: volumes,
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      axisLabel: { color: muted, fontSize: 12, fontWeight: 600 }
    },
    yAxis: {
      type: 'value',
      name: '字节',
      axisLabel: { color: muted, fontSize: 11, formatter: function(v) { return (v / 1000).toFixed(0) + 'K'; } },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [
      {
        name: '最大文件',
        type: 'bar',
        data: maxSizes,
        itemStyle: { color: accent },
        barMaxWidth: 20,
        z: 3
      },
      {
        name: '平均大小',
        type: 'bar',
        data: avgSizes,
        itemStyle: { color: accent + '99' },
        barMaxWidth: 20,
        z: 2
      },
      {
        name: '最小文件',
        type: 'bar',
        data: minSizes,
        itemStyle: { color: accent2 + '66' },
        barMaxWidth: 20,
        z: 1
      }
    ]
  });

  window.addEventListener('resize', function() { chart1.resize(); });

  // --- Chart 2: 优先级矩阵 ---
  var chart2 = echarts.init(document.getElementById('chart-priority'), null, { renderer: 'svg' });

  var items = [
    { name: 'MOC状态更新', urgency: 10, impact: 8, priority: 'P0', color: crit },
    { name: '充实卷4/5', urgency: 8, impact: 9, priority: 'P1', color: high },
    { name: '补全缺失文件', urgency: 7, impact: 7, priority: 'P2', color: high },
    { name: '闭合τ子质量', urgency: 6, impact: 10, priority: 'P3', color: high },
    { name: '框架性→严格', urgency: 5, impact: 8, priority: 'P4', color: med },
    { name: '修复7.4公式', urgency: 6, impact: 7, priority: 'P5', color: med },
    { name: '补充物理概念', urgency: 4, impact: 7, priority: 'P6', color: med },
    { name: '修复编号', urgency: 3, impact: 3, priority: 'P7', color: low }
  ];

  chart2.setOption({
    animation: false,
    tooltip: {
      trigger: 'item',
      appendToBody: true,
      formatter: function(p) {
        return '<strong>' + p.data.name + '</strong><br/>' +
               '紧迫性: ' + p.data.value[0] + '/10<br/>' +
               '影响度: ' + p.data.value[1] + '/10<br/>' +
               '优先级: <strong style="color:' + p.data.color + '">' + p.data.priority + '</strong>';
      }
    },
    grid: { left: 60, right: 30, top: 20, bottom: 50 },
    xAxis: {
      name: '影响度 →',
      nameLocation: 'middle',
      nameGap: 30,
      nameTextStyle: { color: muted, fontSize: 12, fontWeight: 600 },
      min: 0, max: 11,
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      axisLabel: { color: muted, fontSize: 11 },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    yAxis: {
      name: '紧迫性 →',
      nameLocation: 'middle',
      nameGap: 40,
      nameTextStyle: { color: muted, fontSize: 12, fontWeight: 600 },
      min: 0, max: 11,
      axisLine: { lineStyle: { color: rule } },
      axisTick: { show: false },
      axisLabel: { color: muted, fontSize: 11 },
      splitLine: { lineStyle: { color: rule, type: 'dashed' } }
    },
    series: [{
      type: 'scatter',
      symbolSize: function(val) {
        return 16 + (val[0] + val[1]) * 2;
      },
      data: items.map(function(d) {
        return {
          name: d.name,
          value: [d.impact, d.urgency],
          color: d.color,
          priority: d.priority
        };
      }),
      itemStyle: {
        color: function(p) { return p.data.color; },
        opacity: 0.85,
        borderColor: '#fff',
        borderWidth: 2,
        shadowBlur: 6,
        shadowColor: 'rgba(0,0,0,0.1)'
      },
      label: {
        show: true,
        position: 'right',
        formatter: function(p) { return p.data.name; },
        color: muted,
        fontSize: 11,
        fontWeight: 500
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: rule, type: 'dashed', width: 1 },
        data: [
          { yAxis: 5, label: { show: false } },
          { xAxis: 5, label: { show: false } }
        ]
      }
    }]
  });

  window.addEventListener('resize', function() { chart2.resize(); });
})();