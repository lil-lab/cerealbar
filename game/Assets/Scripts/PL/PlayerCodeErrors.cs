using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public static class PlayerCodeErrors {

    public static readonly Dictionary<int, string> ErrorsCodes = new Dictionary<int, string>
    {
        {1,"Could not find closing endfor or endwhile" },
        {2, "Could not find indicated action instruction" },
        {3, "Parameters in while loop no accepted" },
        {4, "Not allowed to have another while or for loop in a while loop" },
    };

}
