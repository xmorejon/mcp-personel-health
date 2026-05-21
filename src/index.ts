import { onSchedule } from "firebase-functions/v2/scheduler";
import * as admin from "firebase-admin";
import { google } from "googleapis";
import { parse } from "csv-parse/sync";

if (admin.apps.length === 0) {
  admin.initializeApp();
}
const db = admin.firestore();

export const processHealthCSVFromDrive = onSchedule({ schedule: "30 11,23 * * *", timeZone: "Europe/Madrid", region: "europe-west3" }, async (_event) => {
  try {
    // 1. Inicialització de l'API de Google Drive
    const auth = new google.auth.GoogleAuth({
      scopes: ["https://www.googleapis.com/auth/drive.readonly"],
    });
    const drive = google.drive({ version: "v3", auth });

    // 2. Data dinàmica per buscar els fitxers d'avui (YYYY.MM.DD)
    const todayMadrid = new Date().toLocaleDateString("en-CA", { timeZone: "Europe/Madrid" }); // Format: YYYY-MM-DD
    const dateStr = todayMadrid.replace(/-/g, "."); // Format: YYYY.MM.DD
    // Compute yesterday in the same time zone
    const yesterday = new Date(new Date().setDate(new Date().getDate() - 1));
    const yesterdayMadrid = yesterday.toLocaleDateString("en-CA", { timeZone: "Europe/Madrid" });
    const yesterdayStr = yesterdayMadrid.replace(/-/g, "."); // Format: YYYY.MM.DD
    console.log('Computed dateStr:', dateStr);

    // 3. Cerca de TOTS els fitxers CSV d'avui en una sola petició
    const fileSearch = await drive.files.list({
      q: `(name contains '${dateStr}' or name contains '${yesterdayStr}') and name contains '.csv' and trashed = false`,
      fields: "files(id, name, mimeType)",
      spaces: "drive",
    });
    console.log('Raw fileSearch response:', fileSearch);

    const files = fileSearch.data.files;
    console.log('Search result files:', files?.map(f => f?.name));
    if (!files || files.length === 0) {
      console.log(`No CSV files found for date ${dateStr}.`);
      return;
    }

    const initDayData = (dateKey: string) => {
      if (!dailyDataMap[dateKey]) {
        dailyDataMap[dateKey] = {
          lastUpdated: admin.firestore.FieldValue.serverTimestamp(),
          date: dateKey,
        };
      }
    };

    // Helper to get the target date key for a file based on its name
    const getDateKeyForFile = (fileName: string): string => {
      if (fileName.includes(yesterdayStr)) return yesterdayMadrid;
      return todayMadrid; // default to today
    };

    // Map to hold aggregated data per date (today and yesterday)
    const dailyDataMap: {
      [date: string]: {
        averageHeartRate?: number;
        lastUpdated: FirebaseFirestore.FieldValue;
        date: string;
        weight?: number;
        steps?: number;
        hrSum?: number;
        hrCount?: number;
        activities?: any[];
      }
    } = {};

    // 4. Bucle pels fitxers i parseig específic segons el nom
    for (const file of files) {
      if (!file.id || !file.name) continue;

      // Defensive check – ensure the file is truly a CSV
      if (!file.name.toLowerCase().endsWith('.csv')) {
        console.log('Skipping non‑CSV file:', file.name);
        continue;
      }

      const fileResponse = await drive.files.get({
        fileId: file.id,
        alt: "media",
      });

      const csvRawText = fileResponse.data as string;
      let records: Record<string, string>[] = [];
      try {
        records = parse(csvRawText, {
          columns: true,
          skip_empty_lines: true,
          delimiter: ','
        }) as Record<string, string>[];
      } catch (e) {
        console.error('CSV parse error for file', file.name, e);
        continue; // skip malformed file
      }

      if (records.length === 0) continue;

      const name = file.name.toUpperCase();
      const dateKey = getDateKeyForFile(file.name);
      initDayData(dateKey);

      if (name.includes("PESO")) {
        // Només ens cal el pes de la primera fila
        const pesoRaw = records[0]["Peso"];
        if (pesoRaw) dailyDataMap[dateKey].weight = parseFloat(pesoRaw);
      } else if (name.includes("FRECUENCIA")) {
        // Calculem la freqüència cardíaca mitjana diària per aquest dia
        for (const row of records) {
          const hrRaw = row["Frecuencia cardiaca"];
          if (hrRaw) {
            dailyDataMap[dateKey].hrSum = (dailyDataMap[dateKey].hrSum || 0) + parseFloat(hrRaw);
            dailyDataMap[dateKey].hrCount = (dailyDataMap[dateKey].hrCount || 0) + 1;
          }
        }
      } else if (name.includes("PASOS")) {
        // Sumem tots els passos parcials per aquest dia
        for (const row of records) {
          const stepsRaw = row["Pasos"];
          if (stepsRaw) {
            dailyDataMap[dateKey].steps = (dailyDataMap[dateKey].steps || 0) + parseInt(stepsRaw, 10);
          }
        }
      } else if (name.includes("RUNNING") || name.includes("WALKING") || name.includes("ACTIVIDADES")) {
        // Guardem l'activitat com a objecte a l'array per aquest dia
        for (const row of records) {
          const activityType = row["Tipo de actividad"] || "UNKNOWN";
          const distance = row["Distancia (km)"];
          const activeTime = row["Tiempo activo"];
          const time = row["Hora"];
          const activity = {
            type: activityType,
            distanceKm: distance ? parseFloat(distance) : 0,
            activeTimeSecs: activeTime ? parseInt(activeTime, 10) : 0,
            time: time || ""
          };
          dailyDataMap[dateKey].activities = (dailyDataMap[dateKey].activities || []).concat(activity);
        }
      }
    }

    // Consolidació final per cada dia
    for (const [dateKey, data] of Object.entries(dailyDataMap)) {
      // Compute average heart rate if data exists
      if (data.hrCount && data.hrCount > 0) {
        data.averageHeartRate = Math.round((data.hrSum || 0) / data.hrCount);
      }
      // Remove helper fields before persisting
      const { hrSum, hrCount, ...persistData } = data;
      const docRef = db.collection("health_metrics").doc(dateKey);
      await docRef.set(persistData, { merge: true });
      console.log('Written data for date', dateKey);
    }

    console.log("Function executed successfully", { parsedFiles: files.length, dates: Object.keys(dailyDataMap) });

  } catch (error) {
    console.error("Error processing CSV ETL:", error);
    // No response needed for scheduled function
  }
});
