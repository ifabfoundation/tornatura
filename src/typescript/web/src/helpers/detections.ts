import { ObservationPoint, ObservationType } from "@tornatura/coreapis";
import { Detection } from "@tornatura/coreapis";
import { mapValues } from "./common";

export function getColorDiseaseIndex(diseaseIndex: number): string {
  const colors = ["#42C318", "#FFB290", "#FF4D4D", "#A10505"];
  return mapColorIndex(diseaseIndex, 0, 0.4, colors);
}

export function getRangePointColorMap(
  v: number,
  rangeMin: number = 0,
  rangeMax: number = 5,
): string {
  const colors = ["#42C318", "#FFB290", "#FF4D4D", "#A10505"];
  return mapColorIndex(v, rangeMin, rangeMax, colors);
}

function mapColorIndex(value: number, min: number, max: number, colors: string[]): string {
  const range = max - min;
  const segment = range / colors.length;
  const index = Math.min(colors.length - 1, Math.floor((value - min) / segment));
  return colors[index];
}

export function enrichedMapPoints(points: ObservationPoint[], observationType: ObservationType) {
  const type = observationType ? observationType.observationType : "null";
  let counterSumMax = 0;
  if (type === "counters") {
    const sumValues = points.map((point) => {
      let countersSum = 0;
      if (point.data && point.data.counters) {
        countersSum = point.data.counters.reduce((a, b) => a + b.counterValue, 0);
      }
      return countersSum;
    });
    counterSumMax = Math.max(...sumValues);
  }

  const enrichedMapPoints = points.map((point: ObservationPoint) => {
    const num = point.data.rangeValue || 0;
    let color: string = "rgba(0,0,0,0.5)";
    let size: number = 7;

    // Change color for type 'range'
    if (type === "range") {
      color = getRangePointColorMap(num);
    }

    // Change size for type 'counters'
    if (type === "counters") {
      let countersSum = 0;
      if (point.data && point.data.counters) {
        countersSum = point.data.counters.reduce((a, b) => a + b.counterValue, 0);
      }
      size = mapValues(countersSum, 0, counterSumMax, 0, 60);
    }

    return {
      lng: point.position.lng,
      lat: point.position.lat,
      size: size,
      color: color,
    };
  });
  return enrichedMapPoints;
}

export function getDetectionStats(detection: Detection) {
  // calculate stats for each detection
  // FOR DATA OF TYPE "RANGE"
  let detectionStats = {
    type: "",
    pointsCount: 0,
    pointsSum: 0,
    pointsMin: Infinity,
    pointsMax: -Infinity,
    pointsAvg: 0,
    infectedPercent: 0,
    infectedPercentStr: "00%",
    intensityAvg: 0,
    intensityAvgStr: "00%",
    diseaseIndex: 0,
    diseaseIndexStr: "00%",
    counterSumsTotal: 0,
    displayLabel: "-",
    displayValue: "-",
  };

  detection.detectionData.points.forEach((point) => {
    const rv = point.data.rangeValue;
    const isValidRangePoint = rv !== undefined && rv !== null;
    if (isValidRangePoint) {
      detectionStats.type = "range";
      detectionStats.pointsCount++;
      detectionStats.pointsSum += rv;
      detectionStats.pointsMin = Math.min(detectionStats.pointsMin, rv);
      detectionStats.pointsMax = Math.max(detectionStats.pointsMax, rv);
    }

    const counters = point.data.counters;
    const isValidCounterPoint = counters !== undefined && counters !== null && counters.length > 0;
    if (isValidCounterPoint) {
      detectionStats.type = "counters";
      const countersSum = counters.reduce((a, b) => a + b.counterValue, 0);
      detectionStats.counterSumsTotal += countersSum;
    }
  });
  detectionStats.pointsAvg =
    detectionStats.pointsCount > 0 ? detectionStats.pointsSum / detectionStats.pointsCount : 0;

  // detection = {
  //   agrifieldId: "685a5d40f2de7db5c17f177c",
  //   creationTime: 1769275022455,
  //   detectionData: {
  //     bbch: "21",
  //     notes: "Lorem ipsum…",
  //     photos: ["https://placehold.co/600x400", "https://placehold.co/600x400"],
  //     points: [{
  //       data: {
  //         counters: [],
  //         rangeValue: 5,
  //       },
  //       position: {lng: 12.76965574474565, lat: 41.68182819504833}
  //     }],
  //   },
  //   detectionTime: 1769275000458,
  //   detectionTypeId: "6974fd8c388f508a98827411",
  //   id: "6974fe8e388f508a98827415",
  //   lastUpdateTime: 1769275022455,
  // }

  // --- pianteColpite

  const infectedCount = detection.detectionData.points.filter(
    (entry: any) => entry.data.rangeValue > 0,
  ).length;
  const infectedPercent = infectedCount / detection.detectionData.points.length;
  detectionStats.infectedPercent = infectedPercent;
  detectionStats.infectedPercentStr = `${(infectedPercent * 100).toFixed(1)}%`;

  // --- intensitaMedia

  const tonyHelpGettingRangeMaxFromObservationType = 5; // TO REPLACE WITH REAL VALUE
  const totalScores = detection.detectionData.points.reduce((acc: number, entry: any) => {
    const normalized = entry.data.rangeValue / tonyHelpGettingRangeMaxFromObservationType;
    return acc + normalized;
  }, 0);
  const avgScore = totalScores / detection.detectionData.points.length;
  const percent = avgScore;
  detectionStats.intensityAvg = percent;
  detectionStats.intensityAvgStr = `${(percent * 100).toFixed(1)}%`;

  detectionStats.diseaseIndex = detectionStats.infectedPercent * detectionStats.intensityAvg;
  detectionStats.diseaseIndexStr = `${(detectionStats.diseaseIndex * 100).toFixed(1)}%`;

  // --- displayValue
  if (detectionStats.type === "range") {
    detectionStats.displayLabel = "Indice di malattia";
    detectionStats.displayValue = detectionStats.diseaseIndexStr;
  } else if (detectionStats.type === "counters") {
    detectionStats.displayLabel = "Totale conteggi";
    detectionStats.displayValue = detectionStats.counterSumsTotal.toString();
  }

  return detectionStats;
}
