<template>
  <v-card class="chart-card" elevation="2" rounded="lg">
    <v-card-title class="chart-title py-3 px-6">
      <v-icon color="primary" class="mr-2">mdi-chart-arc</v-icon>
      教学材料完成率
    </v-card-title>
    <v-card-text class="px-2 pt-0 pb-2">
      <div ref="chartContainer" class="chart-container" style="height: 300px;"></div>
    </v-card-text>
  </v-card>
</template>

<script>
import * as echarts from 'echarts/core';
import { RadarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必要的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  RadarChart,
  CanvasRenderer
]);

export default {
  name: 'MaterialCompletionChart',
  props: {
    radarData: {
      type: Array,
      required: true
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      chart: null
    };
  },
  watch: {
    radarData: {
      handler() {
        this.renderChart();
      },
      deep: true
    }
  },
  mounted() {
    this.initChart();
  },
  beforeUnmount() {
    if (this.chart) {
      this.chart.dispose();
      this.chart = null;
    }
  },
  methods: {
    initChart() {
      // 初始化图表实例
      this.chart = echarts.init(this.$refs.chartContainer);
      this.renderChart();
      
      // 响应窗口大小变化
      window.addEventListener('resize', this.resizeChart);
    },
    resizeChart() {
      if (this.chart) {
        this.chart.resize();
      }
    },
    renderChart() {
      if (!this.chart || !this.radarData || this.radarData.length === 0) return;
      
      const courseNames = this.radarData.map(item => item.name);
      const values = this.radarData.map(item => item.value);
      
      // 配置图表选项
      const option = {
        tooltip: {
          trigger: 'item'
        },
        radar: {
          indicator: courseNames.map(name => ({
            name,
            max: 100
          })),
          center: ['50%', '50%'],
          radius: '65%'
        },
        series: [
          {
            name: '教学材料完成率',
            type: 'radar',
            data: [
              {
                value: values,
                name: '完成率(%)',
                itemStyle: {
                  color: '#42A5F5'
                },
                areaStyle: {
                  color: {
                    type: 'linear',
                    x: 0,
                    y: 0,
                    x2: 0,
                    y2: 1,
                    colorStops: [
                      {
                        offset: 0,
                        color: 'rgba(66, 165, 245, 0.8)'
                      },
                      {
                        offset: 1,
                        color: 'rgba(66, 165, 245, 0.1)'
                      }
                    ]
                  }
                },
                label: {
                  show: true,
                  formatter: '{c}%'
                }
              }
            ]
          }
        ]
      };
      
      // 应用配置
      this.chart.setOption(option);
      
      // 显示加载状态
      if (this.loading) {
        this.chart.showLoading();
      } else {
        this.chart.hideLoading();
      }
    }
  }
};
</script>

<style scoped>
.chart-container {
  width: 100%;
}
.chart-title {
  display: flex;
  align-items: center;
  font-size: 1.1rem;
  font-weight: 500;
  color: #37474f;
}
</style>
