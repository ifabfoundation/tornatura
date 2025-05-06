import { Point } from "@tornatura/coreapis";
import React from "react";
import { Button } from "react-bootstrap";





export function Welcome() {
  const [position, setPosition] = React.useState<Point>();
  
  React.useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition((position) => {
        setPosition({lng: position.coords.longitude, lat: position.coords.latitude});
      });
    } else {
      
    }    
  }, []); 

  return (
    <div>
      <h1>Benvenuto su Tornatura</h1>
      <h2>Hai un account?</h2>
      <Button>Login</Button>
      <h2>Non hai un account registrarti</h2>
      <div className="mb-3"></div>
        <form autoComplete="off">
          <div className="input-row">
            <label>
              Nome
              <input
                id="name"
                name="name"
                type="text"
                placeholder="Name"
              />
            </label>
            <div className="error">Nome richiesto</div>
          </div>
          <div className="input-row">
            <label>
              Type
              <select
                id="typeId"
                name="typeId"
              >
                <option  value=''>Choose a type</option>
                <option  value='pippo'>Pippo</option>
                <option  value='pluto'>Pluto</option>
              </select>
            </label>
          </div>
          <div className="input-row">
            <label>
              Description
              <textarea
                id="description"
                name="description"
                placeholder=""
                rows={15}
                cols={50}
              >
              </textarea>
            </label>
          </div>
          <hr />
          <div className="buttons-wrapper">
            <button className="secondary" onClick={() => {}}>Cancel</button>
            <input type="submit" className="primary" value="Create" />
          </div>
        </form>
    </div>
  );
}