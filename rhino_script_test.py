import rhinoscriptsyntax as rs

def create_intersecting_spheres():
    # Parameters for the first sphere
    center1 = [0, 0, 0]
    radius1 = 10.0
    
    # Parameters for the second sphere
    # We place the second center 12 units away. 
    # Since 10 + 8 = 18 and 12 < 18, they will intersect.
    center2 = [12, 0, 0]
    radius2 = 8.0
    
    # Add the spheres to the document
    sphere1_id = rs.AddSphere(center1, radius1)
    sphere2_id = rs.AddSphere(center2, radius2)
    
    if sphere1_id and sphere2_id:
        print("Successfully created two intersecting spheres.")
        # Select them so you can see them immediately
        rs.SelectObjects([sphere1_id, sphere2_id])
    else:
        print("An error occurred while creating the spheres.")

if __name__ == "__main__":
    create_intersecting_spheres()