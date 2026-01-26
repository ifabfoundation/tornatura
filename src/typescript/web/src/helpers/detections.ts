import { ObservationPoint, ObservationType } from "@tornatura/coreapis";
import { Detection } from "@tornatura/coreapis";

export function getRangePointColor(v: number): string {
  let c = "#43C318";
  if (v > 0.25) c = "#FFB291";
  if (v > 0.5) c = "#FF4D4E";
  if (v > 0.75) c = "#A10406";
  return c;
}

export function getCounterPointSize(): number {
  return 25;
}

export function enrichedMapPoints(points: ObservationPoint[], observationType: ObservationType) {
  const enrichedPoints = points.map((point: ObservationPoint) => {
    const num = point.data.rangeValue || 0;
    const type = observationType ? observationType.observationType : "null";

    let color: string = "black";
    if (type == "range") {
      const rangeMax = observationType
        ? observationType.rangeMax
          ? observationType.rangeMax
          : 5
        : 5;
      color = getRangePointColor(num / rangeMax);
    }

    console.log("observationType", observationType);
    return {
      lng: point.position.lng,
      lat: point.position.lat,
      size: 7,
      color: color,
    };
  });
  return enrichedPoints;
}

export function getDetectionStats(detection: Detection) {
  // calculate stats for each detection
  // FOR DATA OF TYPE "RANGE"
  let detectionStats = {
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
  };
  detection.detectionData.points.forEach((point) => {
    const v = point.data.rangeValue;
    const isValidPoint = v !== undefined && v !== null;
    if (isValidPoint) {
      detectionStats.pointsCount++;
      detectionStats.pointsSum += v;
      detectionStats.pointsMin = Math.min(detectionStats.pointsMin, v);
      detectionStats.pointsMax = Math.max(detectionStats.pointsMax, v);
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

  return detectionStats;
}
