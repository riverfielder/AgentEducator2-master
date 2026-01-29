<template>
  <v-card class="chart-card" elevation="2" rounded="lg">
    <v-card-title class="chart-title py-3 px-6">
      <v-icon color="primary" class="mr-2">mdi-clock-outline</v-icon>
      学习时长分布
    </v-card-title>
    <v-card-text class="px-2 pt-0 pb-2">
      <div ref="chartContainer" class="chart-container" style="height: 300px;"></div>
    </v-card-text>
  </v-card>
</template>

<script>
import * as echarts from 'echarts/core';
import { BarChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

// 注册必要的组件
echarts.use([
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  BarChart,
  CanvasRenderer
]);

export default {
  name: 'StudyTimeChart',
  props: {
    timeData: {
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
    timeData: {
      handler() {
        this.renderChart();
      },
      deep: true
    },
    loading: {
      handler() {
        this.updateLoadingState();
      },
      immediate: true
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
      if (!this.chart || !this.timeData || this.timeData.length === 0) return;
      
      // 提取数据
      const categories = this.timeData.map(item => item.name);
      const values = this.timeData.map(item => item.value);
      
      // 配置图表选项
      const option = {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'shadow'
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: categories,
          axisTick: {
            alignWithLabel: true
          },
          axisLabel: {
            rotate: 30,
            margin: 15
          }
        },
        yAxis: {
          type: 'value',
          name: '学生人数',
          nameTextStyle: {
            padding: [0, 0, 0, 30]
          }
        },
        series: [
          {
            name: '学生数',
            type: 'bar',
            barWidth: '60%',
            data: values,
            itemStyle: {
              color: function(params) {
                // 根据值的大小变化颜色深浅
                const colorList = [
                  '#D3F2EC', '#A1E5D8', '#68D5C0', '#38C4AB', '#1AAD92'
                ];
                const index = Math.min(
                  Math.floor(params.value / 10),
                  colorList.length - 1
                );
                return colorList[index];
              }
            },
            label: {
              show: true,
              position: 'top',
              formatter: '{c}人'
            }
          }
        ]
      };
      
      // 应用配置
      this.chart.setOption(option);
      
      // 更新加载状态
      this.updateLoadingState();
    },
    updateLoadingState() {
      if (!this.chart) return;
      
      // 显示或隐藏加载状态
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
