using System.Collections;
using System.Collections.Generic;
using UnityEngine;

[System.Serializable]
public struct HexCoordinates
{
   

    [SerializeField]
    private int x, z;

    private int r,g, b;

    public int X
    {
        get{ return x; }
    }

    public int Z
    {
        get{ return z; }
    }

    public int R
    {
        get{ return r; }
    }

    public int G
    {
        get{ return g; }
    }

    public int B
    {
        get{ return b; }
    }

    public HexCoordinates(int x, int z)
    {
        this.x = x;
        this.z = z;

        this.r = -1;
        this.g = -1;
        this.b = -1;
    }

    public static HexCoordinates FromOffsetCoords(int x, int z)
    {
        return new HexCoordinates(x, z);

    }

    public static HexCoordinates FromPosition(Vector3 position)
    {
        var x = position.x / (HexMetrics.innerRadius * 2f);
        var y = -x;
        var offset = position.z / (HexMetrics.outerRadius * 2f);
        x -= offset;
        y -= offset;
        var iX = Mathf.RoundToInt(x);
        var iY = Mathf.RoundToInt(y);
        var iZ = Mathf.RoundToInt(-x - y);

        if (iX + iY + iZ != 0)
        {
            var dX = Mathf.Abs(x - iX);
            var dY = Mathf.Abs(y - iY);
            var dZ = Mathf.Abs(-x - y - iZ);

            if (dX > dY && dX > dZ)
            {
                iX = -iY - iZ;
            }
            else if (dZ > dY)
            {
                iZ = -iX - iY;
            }
        }
        return new HexCoordinates(iX, iZ);
    


    }

    public override string ToString()
    {
        return " " + x + ","+z;

    }
}
