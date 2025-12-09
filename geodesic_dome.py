import rhinoscriptsyntax as rs
import math

def create_geodesic_dome(radius, frequency):
    """
    Creates a geodesic sphere (dome) based on an icosahedron with the given radius and frequency.
    """
    
    # Golden ratio
    t = (1.0 + math.sqrt(5.0)) / 2.0
    
    # Base icosahedron vertices (unscaled)
    # These define the 12 vertices of an icosahedron
    base_verts = [
        [-1,  t,  0], [ 1,  t,  0], [-1, -t,  0], [ 1, -t,  0],
        [ 0, -1,  t], [ 0,  1,  t], [ 0, -1, -t], [ 0,  1, -t],
        [ t,  0, -1], [ t,  0,  1], [-t,  0, -1], [-t,  0,  1]
    ]
    
    # Normalize vertices to unit sphere
    base_verts = [rs.VectorUnitize(v) for v in base_verts]
    
    # Icosahedron faces (indices of vertices)
    # 20 faces
    faces = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]
    ]
    
    # We will collect all unique vertices and faces for the new mesh
    mesh_vertices = []
    mesh_face_indices = []
    
    # Helper to get index of a vertex, adding it if it doesn't exist
    # Using a dictionary for faster lookup of existing vertices to merge duplicates
    # Key: (x,y,z) rounded to avoid float precision issues, Value: index
    vert_map = {} 
    
    def get_vert_index(v):
        # Normalize to project onto sphere
        v_unit = rs.VectorUnitize(v)
        # Scale by radius
        v_scaled = rs.VectorScale(v_unit, radius)
        
        # Create a key for the map (rounding for tolerance)
        key = (round(v_scaled[0], 4), round(v_scaled[1], 4), round(v_scaled[2], 4))
        
        if key in vert_map:
            return vert_map[key]
        else:
            idx = len(mesh_vertices)
            mesh_vertices.append(v_scaled)
            vert_map[key] = idx
            return idx

    # Subdivide each face of the icosahedron
    for face in faces:
        v1 = base_verts[face[0]]
        v2 = base_verts[face[1]]
        v3 = base_verts[face[2]]
        
        # We iterate through the grid of the triangle
        # We need to store the indices of the points in this face grid to form triangles
        grid_indices = {}
        
        for row in range(frequency + 1):
            for col in range(frequency - row + 1):
                # Calculate point on the flat triangle face
                # Using vector addition: P = v1 + (col/f) * (v2-v1) + (row/f) * (v3-v1)
                
                vec_col = rs.VectorScale(rs.VectorSubtract(v2, v1), float(col)/frequency)
                vec_row = rs.VectorScale(rs.VectorSubtract(v3, v1), float(row)/frequency)
                
                pt = rs.VectorAdd(v1, rs.VectorAdd(vec_col, vec_row))
                
                # Get the index (this projects it to the sphere and merges duplicates)
                idx = get_vert_index(pt)
                grid_indices[(row, col)] = idx
        
        # Create faces for this subdivision
        for row in range(frequency):
            for col in range(frequency - row):
                # Triangle pointing up (relative to v1)
                # Vertices: (row, col), (row, col+1), (row+1, col)
                i1 = grid_indices[(row, col)]
                i2 = grid_indices[(row, col+1)]
                i3 = grid_indices[(row+1, col)]
                mesh_face_indices.append([i1, i2, i3])
                
                # Triangle pointing down (if not in the last sub-row)
                # Vertices: (row, col+1), (row+1, col+1), (row+1, col)
                if col < frequency - row - 1:
                    i1 = grid_indices[(row, col+1)]
                    i2 = grid_indices[(row+1, col+1)]
                    i3 = grid_indices[(row+1, col)]
                    mesh_face_indices.append([i1, i2, i3])

    # Create the mesh in Rhino
    mesh_id = rs.AddMesh(mesh_vertices, mesh_face_indices)
    return mesh_id

if __name__ == "__main__":
    # Default values
    radius = 10.0
    frequency = 2
    
    # Prompt user for input if running in Rhino
    # These functions return None if the user cancels
    r_input = rs.GetReal("Enter Dome Radius", radius)
    if r_input is not None:
        radius = r_input
        
    f_input = rs.GetInteger("Enter Frequency (Subdivision Level)", frequency)
    if f_input is not None:
        frequency = f_input
        
    rs.EnableRedraw(False)
    mesh = create_geodesic_dome(radius, frequency)
    rs.EnableRedraw(True)
    
    if mesh:
        print("Geodesic dome created with Radius {} and Frequency {}".format(radius, frequency))
        rs.SelectObject(mesh)
