/**
 * checkForCctvTrigger — Auto-trigger CCTV verification for high-confidence wildfires
 *
 * The mock video represents one camera near Jamnagar, Gujarat. Only detections
 * within the configured radius can use this video.
 *
 * @param {Array} features - GeoJSON features array from /api/fires.geojson
 */
const MOCK_CCTV = {
  latitude: 21.90,
  longitude: 69.80,
  radiusDegrees: 0.25,
  videoPath: '/integration/cctv_mock_video.mp4',
  cameraId: 'CAM-JAMNAGAR-01'
};

function isMockCctvLocation(feature) {
  if (!feature || !feature.geometry || !feature.geometry.coordinates) return false;
  const [longitude, latitude] = feature.geometry.coordinates;
  return Math.abs(latitude - MOCK_CCTV.latitude) <= MOCK_CCTV.radiusDegrees &&
    Math.abs(longitude - MOCK_CCTV.longitude) <= MOCK_CCTV.radiusDegrees;
}

function checkForCctvTrigger(features) {
  const highConfidenceWildfire = features.find(f => {
    return f.properties &&
      f.properties.classification === 'wildfire' &&
      f.properties.frp > 80 &&
      isMockCctvLocation(f);
  });

  if (highConfidenceWildfire) {
    // Trigger CCTV verification flow
    console.log('[ThermoWatch] High-confidence wildfire detected. Triggering CCTV lookup...');

    if (typeof showCctvQuerying === 'function') {
      showCctvQuerying();
    } else {
      console.log('Mock: showCctvQuerying() triggered');
    }

    setTimeout(() => {
      if (typeof showCctvConfirmed === 'function') {
        showCctvConfirmed(MOCK_CCTV.videoPath, MOCK_CCTV.cameraId);
      } else {
        console.log(`Mock: showCctvConfirmed('${MOCK_CCTV.videoPath}', '${MOCK_CCTV.cameraId}') triggered`);
      }
      console.log(`[ThermoWatch] CCTV Confirmed: ${MOCK_CCTV.cameraId}`);
    }, 2000); // simulate ~2 second "checking" delay
  } else {
    // No high-confidence wildfire found; reset CCTV panel
    if (typeof resetCctvPanel === 'function') {
      resetCctvPanel();
    }
  }
}

window.isMockCctvLocation = isMockCctvLocation;
window.MOCK_CCTV = MOCK_CCTV;
