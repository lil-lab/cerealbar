using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;
using System.Collections;
using System.Text.RegularExpressions;

// InputFieldMod v1.0
// Thanks to:
// mjkkirschner https://github.com/mjkkirschner/XYZ-Visual-Programming/blob/master/Assets/UI/ExpandingInputField.cs
// zxkne http://answers.unity3d.com/questions/1195865/ui-scrollrect-mask-not-hiding-input-field-caret-an.html#answer-1309469

[ExecuteInEditMode]
[RequireComponent(typeof(InputField))]
[RequireComponent(typeof(LayoutElement))]
public class InputFieldMod : UIBehaviour {
	[Range(1,50)]
	public int textRows = 1;

    [SerializeField]
    public GameObject UI;

	// optional scroll rect parent (manually linked)
	public ScrollRect scrollRect;
	RectTransform scrollRectTransform;
	RectTransform ScrollRectTransform { get { if (scrollRect && !scrollRectTransform) scrollRectTransform = scrollRect.GetComponent<RectTransform>(); return scrollRectTransform; } }

	// parent gameobjects
	CanvasScaler scaler;
	float ScaleFactor { 
        get { 
            if (!scaler) { scaler = GetComponentInParent<CanvasScaler>(); } 
            return scaler ? scaler.scaleFactor : 1; 
        } 
    }

	HorizontalOrVerticalLayoutGroup parentLayout;
	HorizontalOrVerticalLayoutGroup ParentLayout { get { parentLayout = transform.parent.GetComponent<HorizontalOrVerticalLayoutGroup>(); return parentLayout; } }

	// current gameobject components
	LayoutElement inputElement;
	LayoutElement InputElement { get { if (!inputElement) inputElement = GetComponent<LayoutElement>(); return inputElement; } }
	InputField inputField;
	InputField InputField { get { if (!inputField) inputField = GetComponent<InputField>(); return inputField; } }
	RectTransform rect;
	RectTransform Rect { get { if (!rect) rect = GetComponent<RectTransform>(); return rect; } }

	// child gameobjects
	CanvasRenderer caret = null;

	// string replacers
	private Regex colorTags = new Regex("<[^>]*>");
	private Regex keyWords = new Regex("and |assert |break |class |continue |def |del |elif |else |except |exec |finally |for |from |global |if |import |in |is |lambda |not |or |pass |print |raise |return |try |while |yield |None |True |False ");
	private Regex operators = new Regex("<=|>=|!=");
	public Regex definedTriggers { get; set; }

	// register input field events on start
	protected override void Start() {
		InputField.onValueChanged.AddListener(new UnityEngine.Events.UnityAction<string>(ResizeInput));
		InputField.onEndEdit.AddListener(new UnityEngine.Events.UnityAction<string>(Highlight));
		InputField.onValueChanged.AddListener(new UnityEngine.Events.UnityAction<string>(RemoveTags));

    }

	#if UNITY_EDITOR
	Vector2 offsetMin;
	Vector2 offsetMax;
	int fontSize;
	int textRowsOld;
	Vector2 scrollSize;
	#endif

	void Update() {
		#if UNITY_EDITOR
		//(editor only) size adjustment if values have changed
		if (textRows <= 0) textRows = 1;
		if (offsetMin == Vector2.zero || offsetMin != InputField.textComponent.rectTransform.offsetMin ||
			offsetMax == Vector2.zero || offsetMax != InputField.textComponent.rectTransform.offsetMax ||
			fontSize == 0 || fontSize != InputField.textComponent.fontSize ||
			textRowsOld == 0 || textRows != textRowsOld) {


			fontSize = InputField.placeholder.GetComponent<Text>().fontSize = InputField.textComponent.fontSize;
			offsetMin = InputField.placeholder.rectTransform.offsetMin = InputField.textComponent.rectTransform.offsetMin;
			offsetMax = InputField.placeholder.rectTransform.offsetMax = InputField.textComponent.rectTransform.offsetMax;
			textRowsOld = textRows;
			ResizeInput();

		}

		// (editor only) adapt size to scroll rect
		if (scrollRect && (scrollSize == Vector2.zero || scrollSize != ScrollRectTransform.rect.size)) {


            scrollSize = ScrollRectTransform.rect.size;
			ResizeInput();
		}
		#endif

		// fix text selection masking
		if (!caret) {
			Transform caretTransform = InputField.transform.Find(InputField.transform.name + " Input Caret");
			if (caretTransform) {
				Graphic graphic = caretTransform.GetComponent<Graphic>();
				if (!graphic) {
					Image image = caretTransform.gameObject.AddComponent<Image>();
					image.color = new Color(0, 0, 0, 0);
				}
			}
		}
	}

	// string operations
	public void Highlight(string text) {
		InputField.text = colorTags.Replace(InputField.text, @"");
		InputField.text = keyWords.Replace(InputField.text, @"<color=blue>$&</color>");
		InputField.text = operators.Replace(InputField.text, @"<color=red>$&</color>");
		if (definedTriggers != null) {
			InputField.text = definedTriggers.Replace(InputField.text, @"<color=green>$&</color>");
		} 
		InputField.MoveTextEnd(false);
	}

	private void RemoveTags(string text) {
		InputField.text = colorTags.Replace(InputField.text, @"");
	}

	// get text padding (min max vertical offset for size calculation)
	float VerticalOffset { 
        get 
        { 
            return InputField.placeholder.rectTransform.offsetMin.y - InputField.placeholder.rectTransform.offsetMax.y; 
        } 
    }


	// resize input field recttransform
	void ResizeInput() {
		ResizeInput(InputField.text);
	}

	void ResizeInput(string text) {
        float canvasScaleFactor = UI.GetComponent<Canvas>().scaleFactor;

        Canvas.ForceUpdateCanvases();
        scaler = GetComponentInParent<CanvasScaler>();


        // current text settings
        TextGenerationSettings settings = InputField.textComponent.GetGenerationSettings(InputField.textComponent.rectTransform.rect.size);
		settings.generateOutOfBounds = false;
		// current text rect height
		float currentHeight = InputField.textComponent.rectTransform.rect.height;
        // preferred text rect height
        Canvas.ForceUpdateCanvases();
        float preferredHeight = (new TextGenerator().GetPreferredHeight(InputField.text, settings) / canvasScaleFactor);

        float defaultHeight; 

        // default text rect height (fit to scroll parent or expand to fit text)
        if (scrollRect) defaultHeight = ScrollRectTransform.rect.height;
		else defaultHeight = ((new TextGenerator().GetPreferredHeight("", settings) * textRows ) / ScaleFactor);

        // force resize
        if (currentHeight < preferredHeight || currentHeight > preferredHeight) {
			if (preferredHeight > defaultHeight) {
                if (ParentLayout) {
                    InputElement.preferredHeight = preferredHeight;
				} else {
                    Rect.sizeDelta = new Vector2(Rect.rect.width, preferredHeight);
				}
			} else {
                if (ParentLayout) {
                    InputElement.preferredHeight = defaultHeight;
				} else {
                    Rect.sizeDelta = new Vector2(Rect.rect.width, defaultHeight);
				}
			}
		} else {
			if (ParentLayout) {
				InputElement.preferredHeight = defaultHeight;
			} else {
				Rect.sizeDelta = new Vector2(Rect.rect.width, defaultHeight);
			}
		}


        // update scroll rect position
        if (scrollRect) StartCoroutine(ScrollMax());
	}

	// update scroll rect position (after Layout was rebuilt)
	IEnumerator ScrollMax() {
		yield return new WaitForEndOfFrame();
		if (scrollRect != null) scrollRect.verticalNormalizedPosition = 0f;
    }
}
