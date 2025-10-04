import { useEffect } from 'react';
import { useMapEvents } from 'react-leaflet';

const MapClickHandler = ({ isDrawing, onMapClick }) => {
  useMapEvents({
    click: (e) => {
      if (isDrawing) {
        onMapClick(e);
      }
    }
  });

  return null;
};

export default MapClickHandler;
