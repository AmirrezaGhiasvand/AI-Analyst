import { Marquee } from "../ui/marquee"
import { SpotlightReveal } from "../ui/spotlight-reveal"
import { ChartAreaStacked } from "./BackgroundCharts/chart-area-stacked"
import { ChartBarMultiple } from "./BackgroundCharts/chart-bar-multiple"
import { ChartPieLabel } from "./BackgroundCharts/chart-pie-label"
import { ChartRadarGridFill } from "./BackgroundCharts/chart-radar-grid-fill"

export default function SpotlightBackground() {
  return (
    <div className="pointer-events-none fixed top-7 -z-20 grid grid-cols-1 opacity-80">
      <SpotlightReveal size={350} opacity={0.8}>
        <Marquee className="[--duration:60s]">
          <ChartAreaStacked />
          <ChartBarMultiple />
          <ChartPieLabel />
          <ChartRadarGridFill />
        </Marquee>
        <Marquee reverse className="[--duration:60s]">
          <ChartBarMultiple />
          <ChartAreaStacked />
          <ChartRadarGridFill />
          <ChartPieLabel />
        </Marquee>
        <Marquee className="[--duration:60s]">
          <ChartRadarGridFill />
          <ChartBarMultiple />
          <ChartPieLabel />
          <ChartAreaStacked />
        </Marquee>
      </SpotlightReveal>
    </div>
  )
}
