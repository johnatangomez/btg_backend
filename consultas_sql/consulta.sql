SELECT DISTINCT c.nombre, c.apellidos
FROM Cliente c
JOIN Inscripción i ON c.id = i.idCliente
JOIN Producto p ON i.idProducto = p.id
JOIN Disponibilidad d ON p.id = d.idProducto
JOIN Visitan v ON c.id = v.idCliente AND d.idSucursal = v.idSucursal
WHERE NOT EXISTS (
    SELECT 1
    FROM Disponibilidad d2
    WHERE d2.idProducto = p.id
      AND d2.idSucursal NOT IN (
          SELECT v2.idSucursal
          FROM Visitan v2
          WHERE v2.idCliente = c.id
      )
);