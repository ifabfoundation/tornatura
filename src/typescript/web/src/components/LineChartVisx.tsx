import { useEffect, useMemo } from "react";
import { Group } from "@visx/group";
import { scaleTime, scaleLinear } from "@visx/scale";
import { Line, LinePath, Circle } from "@visx/shape";
import { AxisBottom, AxisLeft } from "@visx/axis";
import { useTooltip, /* useTooltipInPortal,  */ Tooltip } from "@visx/tooltip";
import * as allCurves from "@visx/curve";
import { localPoint } from "@visx/event";
import { LinearGradient } from "@visx/gradient";

export type Datum = {
  id: string;
  x: Date;
  y: number;
  color: string;
  displayValue?: string;
  displayLabel?: string;
};

export type LineChartVisxProps = {
  width: number;
  height: number;
  data: Datum[];
  selectedId?: string;
  onSelectPoint?: (point: Datum) => void;
  gradients?: boolean;
  margin?: { top: number; right: number; bottom: number; left: number };
};

export default function LineChartVisx({
  width,
  height,
  data,
  onSelectPoint,
  selectedId,
  gradients = false,
  margin = { top: 20, right: 20, bottom: 40, left: 50 },
}: LineChartVisxProps) {
  // const { containerRef, containerBounds, TooltipInPortal } = useTooltipInPortal({
  //   scroll: true,
  //   detectBounds: true,
  // });
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

  useEffect(() => {
    if (!data.length) return;
    // const p = data[data.length - 1]; // default point
    const p = data[0]; // default point
    showTooltip({
      tooltipData: p,
      tooltipLeft: xScale(xAccessor(p).getTime()) - 40,
      tooltipTop: yScale(yAccessor(p)) - 70,
    });
  }, [data, xScale, yScale]);

  function handleMouseMove(event: React.MouseEvent<SVGCircleElement, MouseEvent>, d: Datum) {
    const coords = localPoint(event);
    if (!coords) return;

    showTooltip({
      tooltipData: d,
      tooltipLeft: coords.x,
      tooltipTop: coords.y,
    });
  }

  //   const gradients = useMemo(() => {
  //   return points.slice(0, -1).map((a, i) => {
  //     const b = points[i + 1];
  //     return (
  //       <linearGradient
  //         key={`g-${uid.current}-${i}`}
  //         id={`g-${uid.current}-${i}`}
  //         gradientUnits="userSpaceOnUse"
  //         x1={a.x}
  //         y1={a.y}
  //         x2={b.x}
  //         y2={b.y}
  //       >
  //         <stop offset="0%" stopColor={a.color} />
  //         <stop offset="100%" stopColor={b.color} />
  //       </linearGradient>
  //     );
  //   });
  // }, [points]);

  const yTop = 0; // or chart padding
  const yBottom = height; // or innerHeight if using margins

  return (
    <div className="graph-visx" /* ref={containerRef} */>
      <svg width={width} height={height}>
        <defs>
          {gradients &&
            data.slice(0, -1).map((point, i) => {
              const next = data[i + 1];
              return (
                <LinearGradient
                  key={`grad-${i}`}
                  id={`grad-${i}`}
                  from={next.color}
                  to={point.color}
                  x1="0%"
                  x2="100%"
                  y1="0%"
                  y2="0%"
                />
              );
            })}
        </defs>

        <Group left={margin.left} top={margin.top}>
          {/* Axes */}
          <AxisBottom
            top={innerHeight}
            scale={xScale}
            numTicks={5}
            tickFormat={(d) =>
              new Date(d as number).toLocaleDateString("en-GB", {
                day: "2-digit",
                month: "2-digit",
                year: "2-digit",
              })
            }
          />

          <AxisLeft scale={yScale} numTicks={5} />

          {/* grid */}
          {data.slice(0, -1).map((point, i) => {
            const x = xScale(xAccessor(point).getTime());
            return (
              <Line
                key={`vline-${i}`}
                from={{ x, y: yTop }}
                to={{ x, y: yBottom }}
                stroke="#ccc"
                strokeWidth={1}
                strokeDasharray="4 4" // optional
                // opacity={0.8} // optional
              />
            );
          })}

          {/* Line v2 */}
          {data.slice(0, -1).map((point, i) => {
            const next = data[i + 1];
            const segmentData = [point, next];
            return (
              <LinePath
                key={`segment-${i}`}
                data={segmentData}
                x={(d) => xScale(xAccessor(d).getTime())}
                y={(d) => yScale(yAccessor(d))}
                stroke={gradients ? `url(#grad-${i})` : "black"}
                strokeWidth={8}
                curve={allCurves.curveNatural} // or your curve of choice
              />
            );
          })}
          {/* Line v1 */}
          {/* <LinePath<Datum>
            data={data}
            x={(d) => xScale(xAccessor(d).getTime())}
            y={(d) => yScale(yAccessor(d))}
            stroke={"black"}
            strokeWidth={4}
          /> */}

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
                fill={d.color}
                stroke={selectedId === d.id ? "black" : "#111"}
                strokeWidth={selectedId === d.id ? 3 : 1.5}
                style={{ cursor: onSelectPoint ? "pointer" : "default" }}
                onClick={() => onSelectPoint?.(d)}
                onMouseMove={(e) => handleMouseMove(e, d)}
                onMouseLeave={hideTooltip}
              />
            );
          })}
        </Group>
      </svg>
      {tooltipData && (
        <Tooltip
          top={tooltipTop}
          left={tooltipLeft}
          style={{
            position: "absolute",
            zIndex: 10,
            background: "white",
            border: "1px solid #ccc",
            padding: "6px 10px",
            borderRadius: 4,
            fontSize: 12,
            // transform: "translate(-50%, -100%)",
          }}
        >
          <div>
            <span className="font-s-600 white-space-nowrap">{tooltipData.displayLabel}</span>
            <br />
            <strong className="font-l-600">{tooltipData.displayValue}</strong>
          </div>
          {/* <div>x: {xScale(tooltipData.x)}</div>
          <div>y: {tooltipData.y}</div> */}
        </Tooltip>
      )}
    </div>
  );
}
