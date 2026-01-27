import { useMemo } from "react";
import { Group } from "@visx/group";
import { scaleTime, scaleLinear } from "@visx/scale";
import { LinePath, Circle } from "@visx/shape";
import { AxisBottom, AxisLeft } from "@visx/axis";
import { useTooltip, TooltipWithBounds } from "@visx/tooltip";
import { localPoint } from "@visx/event";

export type Datum = {
  id: string;
  x: Date;
  y: number;
  displayValue?: string;
};

export type InteractiveTimeSeriesChartProps = {
  width: number;
  height: number;
  data: Datum[];
  selectedId?: string;
  onSelectPoint?: (point: Datum) => void;
  margin?: { top: number; right: number; bottom: number; left: number };
};

export default function InteractiveTimeSeriesChart({
  width,
  height,
  data,
  onSelectPoint,
  selectedId,
  margin = { top: 20, right: 20, bottom: 40, left: 50 },
}: InteractiveTimeSeriesChartProps) {
  const { tooltipData, tooltipLeft, tooltipTop, showTooltip, hideTooltip } = useTooltip<Datum>();

  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  // Accessors
  const xAccessor = (d: Datum) => d.x;
  const yAccessor = (d: Datum) => d.y;

  // Scales
  const xScale = useMemo(
    () =>
      scaleTime<number>({
        domain: [
          Math.min(...data.map((d) => xAccessor(d).getTime())),
          Math.max(...data.map((d) => xAccessor(d).getTime())),
        ],
        range: [0, innerWidth],
      }),
    [data, innerWidth],
  );

  const yScale = useMemo(
    () =>
      scaleLinear<number>({
        domain: [Math.min(...data.map(yAccessor)), Math.max(...data.map(yAccessor))],
        nice: true,
        range: [innerHeight, 0],
      }),
    [data, innerHeight],
  );

  function handleMouseMove(event: React.MouseEvent<SVGCircleElement, MouseEvent>, d: Datum) {
    const coords = localPoint(event);
    if (!coords) return;

    showTooltip({
      tooltipData: d,
      tooltipLeft: coords.x,
      tooltipTop: coords.y,
    });
  }

  return (
    <div style={{ position: "relative" }}>
      <svg width={width} height={height}>
        <Group left={margin.left} top={margin.top}>
          {/* Line */}
          <LinePath<Datum>
            data={data}
            x={(d) => xScale(xAccessor(d).getTime())}
            y={(d) => yScale(yAccessor(d))}
            stroke="#4f83ff"
            strokeWidth={2}
          />

          {/* Points */}
          {data.map((d, i) => {
            const cx = xScale(xAccessor(d).getTime());
            const cy = yScale(yAccessor(d));

            return (
              <Circle
                key={i}
                cx={cx}
                cy={cy}
                r={selectedId === d.id ? 7 : 5}
                fill="#4f83ff"
                stroke={selectedId === d.id ? "black" : "white"}
                strokeWidth={selectedId === d.id ? 3 : 1.5}
                style={{ cursor: onSelectPoint ? "pointer" : "default" }}
                onClick={() => onSelectPoint?.(d)}
                onMouseMove={(e) => handleMouseMove(e, d)}
                onMouseLeave={hideTooltip}
              >
                <title>{d.displayValue}</title>
              </Circle>
            );
          })}

          {/* Axes */}
          <AxisBottom
            top={innerHeight}
            scale={xScale}
            numTicks={5}
            tickFormat={(d) => new Date(d as number).toLocaleDateString()}
          />

          <AxisLeft scale={yScale} numTicks={5} />
        </Group>
      </svg>
      {tooltipData && (
        <TooltipWithBounds
          top={tooltipTop}
          left={tooltipLeft}
          style={{
            position: "absolute",
            background: "white",
            border: "1px solid #ccc",
            padding: "6px 10px",
            borderRadius: 4,
            fontSize: 12,
          }}
        >
          <div>
            <strong>Value:</strong> {tooltipData.displayValue}
          </div>
          {/* <div>x: {xScale(tooltipData.x)}</div>
          <div>y: {tooltipData.y}</div> */}
        </TooltipWithBounds>
      )}
    </div>
  );
}
